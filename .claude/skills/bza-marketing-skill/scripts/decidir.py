#!/usr/bin/env python3
"""Aplica las reglas de inversión Google vs Meta sobre los KPI semanales.

Uso:
    python3 decidir.py kpis.json [--config config.json] [--salida decision.json]

Las reglas viven en `assets/config.json` -> `reglas` y están explicadas en
`references/reglas-decision.md`. `pendientes_fase0` lista los puntos de la Fase 0
sin `hecho: true`; mientras no hay inversión, cada uno es una acción de prioridad alta.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import bza_datos as bd

NOMBRES = {"google_ads": "Google Ads", "meta_ads": "Meta Ads"}


def _cpcc(semana: Dict[str, Any]) -> float:
    """CPCC de una semana; infinito si hubo gasto sin conversaciones calificadas."""
    if semana["cpcc_mxn"] is not None:
        return semana["cpcc_mxn"]
    return math.inf if semana["inversion_mxn"] > 0 else math.nan


def _ultimas(historial: List[Dict[str, Any]], n: int) -> List[Dict[str, Any]]:
    return historial[-n:] if len(historial) >= n else []


def _reparto_actual(pagados: Dict[str, Any]) -> Optional[Dict[str, float]]:
    ultima = {c: (p["historial"][-1]["inversion_mxn"] if p["historial"] else 0.0) for c, p in pagados.items()}
    base = ultima if sum(ultima.values()) > 0 else {c: p["inversion_acumulada"] for c, p in pagados.items()}
    total = sum(base.values())
    if not total:
        return None
    return {c: round(v / total, 3) for c, v in base.items()}


def _transferir(reparto: Dict[str, float], hacia: str, desde: str, reglas: Dict[str, Any]) -> float:
    nuevo_desde = max(reparto[desde] * (1 - reglas["transferencia"]), reglas["piso_canal"])
    monto = round(max(reparto[desde] - nuevo_desde, 0.0), 3)
    reparto[desde] = round(reparto[desde] - monto, 3)
    reparto[hacia] = round(reparto[hacia] + monto, 3)
    return monto


def pendientes_fase0(config: Dict[str, Any]) -> List[Dict[str, str]]:
    """Puntos de `config["pendientes_fase0"]` que todavía no tienen `hecho: true`."""
    return [{"id": p["id"], "texto": p["texto"]}
            for p in config.get("pendientes_fase0", []) if not p.get("hecho")]


def decidir(kpis: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    reglas = config["reglas"]
    presupuesto = config["presupuesto"]
    pagados = kpis["pagados"]
    acciones: List[Dict[str, str]] = []
    alertas: List[str] = []
    estados: Dict[str, str] = {}
    n = reglas["semanas_consecutivas"]

    hay_inversion = any(p["inversion_acumulada"] > 0 for p in pagados.values())
    reparto_actual = _reparto_actual(pagados)
    pendientes = pendientes_fase0(config)

    if not hay_inversion:
        estado = "sin_inversion"
        reparto_sugerido = dict(presupuesto["reparto_inicial"])
        diario = presupuesto["diario_total_fase1_mxn"]
        acciones.append({"prioridad": "alta", "texto": (
            "Completar la Fase 0 (Search Console, GA4, aviso de privacidad, landing por servicio) y aprobar "
            f"el presupuesto de validación: {bd.mxn(diario * reparto_sugerido['google_ads'])} diarios en Google Search y "
            f"{bd.mxn(diario * reparto_sugerido['meta_ads'])} diarios en retargeting de Meta.")})
        for pendiente in pendientes:
            acciones.append({"prioridad": "alta", "texto": f"Fase 0 pendiente: {pendiente['texto']}"})
        for canal in pagados:
            estados[canal] = "sin_inversion"
    else:
        reparto_sugerido = dict(reparto_actual or presupuesto["reparto_inicial"])
        for canal in bd.CANALES_PAGADOS:
            info = pagados[canal]
            if info["inversion_acumulada"] <= 0:
                estados[canal] = "sin_inversion"
                continue
            en_aprendizaje = (info["dias_activo"] < reglas["dias_minimos"]
                              or info["calificadas_acumuladas"] < reglas["calificadas_minimas"])
            estados[canal] = "aprendizaje" if en_aprendizaje else "evaluable"
            recientes = [s for s in _ultimas(info["historial"], n) if s["inversion_mxn"] > 0]
            if len(recientes) == n and all(_cpcc(s) > reglas["cpcc_maximo_mxn"] for s in recientes):
                alertas.append(
                    f"{NOMBRES[canal]} supera el CPCC máximo de {bd.mxn(reglas['cpcc_maximo_mxn'])} "
                    f"{n} semanas seguidas: pausar o rehacer anuncios, palabras clave y landing.")
            if en_aprendizaje:
                acciones.append({"prioridad": "media", "texto": (
                    f"{NOMBRES[canal]} sigue en aprendizaje ({info['dias_activo']} días, "
                    f"{info['calificadas_acumuladas']} calificadas): no mover presupuesto; "
                    "revisar términos de búsqueda, anuncios y landing.")})

        if all(estados[c] == "evaluable" for c in bd.CANALES_PAGADOS):
            estado = "decision"
            for hacia, desde in (("google_ads", "meta_ads"), ("meta_ads", "google_ads")):
                a = _ultimas(pagados[hacia]["historial"], n)
                b = _ultimas(pagados[desde]["historial"], n)
                if len(a) < n or len(b) < n:
                    continue
                pares = list(zip(a, b))
                if all(sa["inversion_mxn"] > 0 and sb["inversion_mxn"] > 0
                       and _cpcc(sa) <= (1 - reglas["ventaja_relativa"]) * _cpcc(sb)
                       and math.isfinite(_cpcc(sa)) for sa, sb in pares):
                    monto = _transferir(reparto_sugerido, hacia, desde, reglas)
                    if monto > 0:
                        acciones.append({"prioridad": "alta", "texto": (
                            f"Mover {monto * 100:.0f} puntos del presupuesto de {NOMBRES[desde]} a "
                            f"{NOMBRES[hacia]}: su CPCC fue al menos {reglas['ventaja_relativa'] * 100:.0f}% menor "
                            f"{n} semanas seguidas.")})
                    break
            else:
                acciones.append({"prioridad": "media", "texto": (
                    "Ningún canal tiene ventaja sostenida de CPCC: mantener el reparto y probar un anuncio nuevo por canal.")})
        else:
            estado = "aprendizaje"

    embudo = kpis["embudo"]
    contenido = kpis["contenido"]
    prospeccion = kpis["prospeccion"]
    if (prospeccion["contactos_acumulados"] >= reglas["alarma_contactos"]
            and contenido["semanas_con_contenido"] >= reglas["alarma_semanas_contenido"]
            and embudo["calificadas_totales"] < reglas["alarma_calificadas_minimas"]):
        alertas.append(
            f"Alarma de oferta: {prospeccion['contactos_acumulados']:.0f} contactos y "
            f"{contenido['semanas_con_contenido']} semanas de contenido con solo "
            f"{embudo['calificadas_totales']} conversaciones calificadas. Revisar oferta y segmento antes de invertir más.")

    if contenido["suficiente"]:
        if contenido["repetir"]:
            acciones.append({"prioridad": "media", "texto": (
                "Producir 1–2 piezas nuevas sobre los temas con más señales fuertes: "
                + ", ".join(contenido["repetir"]) + ".")})
        if contenido["revisar"]:
            acciones.append({"prioridad": "baja", "texto": (
                "Cambiar gancho o formato de los temas con menos señales: " + ", ".join(contenido["revisar"]) + ".")})

    textos_meta = {
        "publicaciones": "Programar las publicaciones que faltan para cumplir 3 por semana.",
        "contactos_personalizados": "Completar los contactos personalizados de prospección (25 minutos al día).",
        "tasa_respuesta_prospeccion": "La tasa de respuesta está baja: abrir con una observación concreta del negocio, no con la oferta.",
        "conversaciones_calificadas": "Faltan conversaciones calificadas: reforzar la llamada a la acción con palabra clave y responder el mismo día.",
        "diagnosticos": "Convertir conversaciones calificadas en diagnósticos de 30 minutos.",
        "propuestas": "Enviar propuesta en menos de 24 horas después de cada diagnóstico.",
    }
    for meta in kpis["metas"]:
        if meta["cumple"] is False:
            acciones.append({"prioridad": "media", "texto": textos_meta[meta["indicador"]]})

    # Con gasto real se conserva el presupuesto diario de la última semana; sin gasto, la referencia de fase 1.
    gasto_ultima = sum(p["historial"][-1]["inversion_mxn"] for p in pagados.values() if p["historial"])
    diario = round(gasto_ultima / 7, 2) if gasto_ultima else presupuesto["diario_total_fase1_mxn"]
    orden = {"alta": 0, "media": 1, "baja": 2}
    acciones.sort(key=lambda a: orden[a["prioridad"]])
    return {
        "semana_inicio": kpis["semana_inicio"],
        "estado": estado,
        "estados_canal": estados,
        "reparto_actual": reparto_actual,
        "reparto_sugerido": reparto_sugerido,
        "diario_sugerido_mxn": {c: round(diario * v, 2) for c, v in reparto_sugerido.items()},
        "alertas": alertas,
        "pendientes_fase0": pendientes,
        "acciones": acciones,
        "datos_faltantes": kpis["datos_faltantes"],
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("kpis", type=Path)
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--salida", type=Path, default=None)
    args = parser.parse_args(argv)
    kpis = json.loads(args.kpis.read_text(encoding="utf-8"))
    resultado = json.dumps(decidir(kpis, bd.cargar_config(args.config)), ensure_ascii=False, indent=2)
    if args.salida:
        args.salida.write_text(resultado + "\n", encoding="utf-8")
    else:
        print(resultado)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Genera el reporte semanal en Markdown a partir de KPI y decisión.

Uso:
    python3 reporte.py kpis.json decision.json [--salida reporte.md]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import bza_datos as bd

MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
ESTADOS = {
    "sin_inversion": "Sin inversión pagada (Fase 0)",
    "aprendizaje": "Aprendizaje: aún no hay datos suficientes para mover presupuesto",
    "decision": "Decisión: hay datos suficientes para reasignar",
}
NOMBRES_CANAL = {
    "facebook": "Facebook", "instagram": "Instagram", "google_ads": "Google Ads",
    "meta_ads": "Meta Ads", "google_organico": "Google orgánico", "sitio": "Sitio (GA4)",
    "prospeccion": "Prospección",
}
NOMBRES_META = {
    "publicaciones": "Publicaciones", "contactos_personalizados": "Contactos personalizados",
    "tasa_respuesta_prospeccion": "Tasa de respuesta de prospección",
    "conversaciones_calificadas": "Conversaciones calificadas", "diagnosticos": "Diagnósticos",
    "propuestas": "Propuestas",
}


def _fecha_corta(iso: str) -> str:
    dia = dt.date.fromisoformat(iso)
    return f"{dia.day} {MESES[dia.month - 1]} {dia.year}"


def _entero(valor: float) -> str:
    return f"{valor:,.0f}"


def _variacion(actual: float, previa: float) -> str:
    if not previa:
        return "nuevo" if actual else "—"
    cambio = (actual - previa) / previa
    return f"{'+' if cambio >= 0 else ''}{cambio * 100:.0f}%"


def _valor_meta(indicador: str, valor: Optional[float]) -> str:
    if valor is None:
        return "—"
    return bd.pct(valor) if indicador.startswith("tasa") else _entero(valor)


def generar(kpis: Dict[str, Any], decision: Dict[str, Any]) -> str:
    lineas: List[str] = []
    agregar = lineas.append
    embudo = kpis["embudo"]
    semana = embudo["semana"]

    agregar(f"# Reporte semanal BZA Creative — {_fecha_corta(kpis['semana_inicio'])} al {_fecha_corta(kpis['semana_fin'])}")
    agregar("")
    agregar("## Resumen")
    agregar("")
    agregar(f"- **Conversaciones:** {semana['conversaciones']} nuevas, {semana['calificadas']} calificadas, "
            f"{semana['propuestas']} con propuesta y {semana['ganados']} ganadas "
            f"({bd.mxn(semana['valor_ganado_mxn'])}).")
    agregar(f"- **Pipeline abierto:** {bd.mxn(embudo['valor_pipeline_mxn'])} estimados; "
            f"{embudo['calificadas_totales']} conversaciones calificadas desde el inicio.")
    agregar(f"- **Inversión:** {ESTADOS[decision['estado']]}.")
    if decision.get("pendientes_fase0"):
        abiertos = len(decision["pendientes_fase0"])
        agregar(f"- **Fase 0:** {abiertos} {'pendiente' if abiertos == 1 else 'pendientes'} (ver abajo).")
    if decision["alertas"]:
        agregar(f"- **Alertas:** {len(decision['alertas'])} (ver abajo).")
    agregar("")

    if decision["alertas"]:
        agregar("## Alertas")
        agregar("")
        for alerta in decision["alertas"]:
            agregar(f"- {alerta}")
        agregar("")

    agregar("## Metas de la semana")
    agregar("")
    agregar("| Indicador | Meta | Real | Estado |")
    agregar("|---|---:|---:|---|")
    for meta in kpis["metas"]:
        estado = "Sin datos" if meta["cumple"] is None else ("Cumple" if meta["cumple"] else "Debajo")
        agregar(f"| {NOMBRES_META[meta['indicador']]} | {_valor_meta(meta['indicador'], meta['meta'])} | "
                f"{_valor_meta(meta['indicador'], meta['real'])} | {estado} |")
    agregar("")

    agregar("## Canales")
    agregar("")
    if kpis["canales"]:
        agregar("| Canal | Inversión | Alcance | Interacciones | Clics | Mensajes | Clics WhatsApp | Alcance vs semana previa |")
        agregar("|---|---:|---:|---:|---:|---:|---:|---:|")
        for canal, info in kpis["canales"].items():
            if canal == "prospeccion":
                continue
            s, p = info["semana"], info["previa"]
            agregar(f"| {NOMBRES_CANAL.get(canal, canal)} | {bd.mxn(s['inversion_mxn'])} | {_entero(s['alcance'])} | "
                    f"{_entero(s['interacciones'])} | {_entero(s['clics'])} | {_entero(s['mensajes'])} | "
                    f"{_entero(s['clics_whatsapp'])} | {_variacion(s['alcance'], p['alcance'])} |")
    else:
        agregar("Sin métricas registradas.")
    agregar("")

    if embudo["por_canal"]:
        agregar("### Conversaciones por origen")
        agregar("")
        agregar("| Origen | Conversaciones | Calificadas |")
        agregar("|---|---:|---:|")
        for canal, valores in sorted(embudo["por_canal"].items(), key=lambda kv: -kv[1]["calificadas"]):
            agregar(f"| {NOMBRES_CANAL.get(canal, canal)} | {valores['conversaciones']} | {valores['calificadas']} |")
        agregar("")
    if embudo["palabras_clave"]:
        agregar("Palabras clave recibidas: " + ", ".join(f"`{k}` ({v})" for k, v in embudo["palabras_clave"].items()) + ".")
        agregar("")

    agregar("## Google vs Meta")
    agregar("")
    for canal, info in kpis["pagados"].items():
        nombre = NOMBRES_CANAL[canal]
        estado = decision["estados_canal"].get(canal, "sin_inversion")
        if info["inversion_acumulada"] <= 0:
            agregar(f"- **{nombre}:** sin inversión.")
            continue
        agregar(f"- **{nombre}:** {bd.mxn(info['inversion_acumulada'])} invertidos en {info['dias_activo']} días, "
                f"{info['calificadas_acumuladas']} calificadas, CPCC acumulado {bd.mxn(info['cpcc_acumulado'])} "
                f"(estado: {estado}).")
    actual = decision["reparto_actual"]
    sugerido = decision["reparto_sugerido"]
    agregar("")
    agregar("| Canal | Reparto actual | Reparto sugerido | Diario sugerido |")
    agregar("|---|---:|---:|---:|")
    for canal in sugerido:
        agregar(f"| {NOMBRES_CANAL[canal]} | {bd.pct(actual[canal]) if actual else '—'} | {bd.pct(sugerido[canal])} | "
                f"{bd.mxn(decision['diario_sugerido_mxn'][canal])} |")
    agregar("")

    contenido = kpis["contenido"]
    agregar("## Contenido orgánico")
    agregar("")
    agregar(f"Publicaciones en la semana: {contenido['publicaciones_semana']}. "
            f"Ventana analizada: {_fecha_corta(contenido['ventana'][0])} a {_fecha_corta(contenido['ventana'][1])}.")
    agregar("")
    if contenido["ranking"]:
        agregar("| Tema | Alcance | Señales fuertes | Mensajes con palabra | Tasa de señal |")
        agregar("|---|---:|---:|---:|---:|")
        for fila in contenido["ranking"]:
            agregar(f"| {fila['tema']} | {_entero(fila['alcance'])} | {_entero(fila['senales_fuertes'])} | "
                    f"{_entero(fila['mensajes_palabra_clave'])} | {bd.pct(fila['tasa_senal'])} |")
        agregar("")
        agregar("Señales fuertes = guardados + compartidos + mensajes con palabra clave. Los “me gusta” no deciden.")
    else:
        agregar("Sin datos por publicación todavía.")
    agregar("")

    pendientes = decision.get("pendientes_fase0") or []
    if pendientes:
        agregar("## Pendientes de la Fase 0")
        agregar("")
        for pendiente in pendientes:
            agregar(f"- [ ] {pendiente['texto']}")
        agregar("")
        agregar("Cuando el responsable confirme un punto, marcar `\"hecho\": true` en `.claude/skills/bza-marketing-skill/assets/config.json` → `pendientes_fase0`.")
        agregar("")

    agregar("## Acciones para esta semana")
    agregar("")
    if decision["acciones"]:
        for numero, accion in enumerate(decision["acciones"], start=1):
            agregar(f"{numero}. **[{accion['prioridad']}]** {accion['texto']}")
    else:
        agregar("Sin acciones nuevas: mantener el plan.")
    agregar("")

    if decision["datos_faltantes"]:
        agregar("## Datos faltantes")
        agregar("")
        for faltante in decision["datos_faltantes"]:
            agregar(f"- {faltante}")
        agregar("")
    return "\n".join(lineas)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("kpis", type=Path)
    parser.add_argument("decision", type=Path)
    parser.add_argument("--salida", type=Path, default=None)
    args = parser.parse_args(argv)
    texto = generar(json.loads(args.kpis.read_text(encoding="utf-8")),
                    json.loads(args.decision.read_text(encoding="utf-8")))
    if args.salida:
        args.salida.write_text(texto, encoding="utf-8")
    else:
        print(texto)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Calcula los KPI semanales de BZA Creative a partir de `marketing/datos/`.

Uso:
    python3 kpis.py [--semana AAAA-MM-DD] [--datos DIR] [--salida kpis.json]

La semana es de lunes a domingo; cualquier fecha dentro de ella sirve. Sin
`--semana` se usa la última semana completa en hora de Ciudad de México.
Termina con código 2 si algún CSV tiene datos inválidos (el mensaje dice archivo y fila).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

import bza_datos as bd

METRICAS_SUMABLES = bd.NUMERICAS["metricas"]


def _sumar(filas: List[Dict[str, str]]) -> Dict[str, float]:
    total = {m: 0.0 for m in METRICAS_SUMABLES}
    for fila in filas:
        for metrica in METRICAS_SUMABLES:
            total[metrica] += bd.numero(fila.get(metrica))
    return total


def _tasas(total: Dict[str, float]) -> Dict[str, Optional[float]]:
    def dividir(a: float, b: float) -> Optional[float]:
        return round(a / b, 4) if b else None

    return {
        "tasa_interaccion": dividir(total["interacciones"], total["alcance"]),
        "ctr": dividir(total["clics"], total["impresiones"]),
        "cpc_mxn": dividir(total["inversion_mxn"], total["clics"]),
    }


def _metricas_por_canal(metricas, semana, previa) -> Dict[str, Any]:
    agrupado: Dict[str, Dict[dt.date, List[Dict[str, str]]]] = defaultdict(lambda: defaultdict(list))
    for fila in metricas:
        agrupado[fila["canal"]][bd.lunes(bd.fecha(fila["semana_inicio"]))].append(fila)
    canales = {}
    for canal, por_semana in sorted(agrupado.items()):
        actual = _sumar(por_semana.get(semana, []))
        anterior = _sumar(por_semana.get(previa, []))
        canales[canal] = {
            "con_datos": semana in por_semana,
            "semana": {**actual, **_tasas(actual)},
            "previa": {**anterior, **_tasas(anterior)},
        }
    return canales, agrupado


def _historial_pagado(canal, agrupado, conversaciones, semana) -> Dict[str, Any]:
    inversion_por_semana = {
        lunes_semana: _sumar(filas)["inversion_mxn"]
        for lunes_semana, filas in agrupado.get(canal, {}).items()
        if lunes_semana <= semana
    }
    con_gasto = sorted(s for s, v in inversion_por_semana.items() if v > 0)
    calificadas_por_semana: Dict[dt.date, int] = defaultdict(int)
    for conv in conversaciones:
        if conv["canal"] == canal and bd.es_si(conv["calificada"]):
            calificadas_por_semana[bd.lunes(bd.fecha(conv["fecha"]))] += 1

    resultado: Dict[str, Any] = {
        "inicio": None, "dias_activo": 0, "historial": [],
        "inversion_acumulada": 0.0, "calificadas_acumuladas": 0, "cpcc_acumulado": None,
    }
    if not con_gasto:
        return resultado
    inicio = con_gasto[0]
    for lunes_semana in bd.semanas(inicio, semana):
        inversion = inversion_por_semana.get(lunes_semana, 0.0)
        calificadas = calificadas_por_semana.get(lunes_semana, 0)
        resultado["historial"].append({
            "semana": lunes_semana.isoformat(),
            "inversion_mxn": inversion,
            "calificadas": calificadas,
            "cpcc_mxn": round(inversion / calificadas, 2) if calificadas else None,
        })
        resultado["inversion_acumulada"] += inversion
        resultado["calificadas_acumuladas"] += calificadas
    fin = semana + dt.timedelta(days=6)
    resultado["inicio"] = inicio.isoformat()
    resultado["dias_activo"] = (fin - inicio).days + 1
    if resultado["calificadas_acumuladas"]:
        resultado["cpcc_acumulado"] = round(
            resultado["inversion_acumulada"] / resultado["calificadas_acumuladas"], 2)
    return resultado


def _embudo(conversaciones, semana) -> Dict[str, Any]:
    fin = semana + dt.timedelta(days=6)
    de_semana = [c for c in conversaciones if semana <= bd.fecha(c["fecha"]) <= fin]

    def en_semana(etapa: str) -> List[Dict[str, str]]:
        """Conversaciones (iniciadas en cualquier semana) que llegaron a `etapa` en esta."""
        filas = []
        for conv in conversaciones:
            dia = bd.fecha_etapa(conv, etapa)
            if dia is not None and semana <= dia <= fin:
                filas.append(conv)
        return filas

    ganadas = en_semana("ganado")
    por_canal: Dict[str, Dict[str, int]] = defaultdict(lambda: {"conversaciones": 0, "calificadas": 0})
    for conv in de_semana:
        canal = conv["canal"] or "sin_canal"
        por_canal[canal]["conversaciones"] += 1
        por_canal[canal]["calificadas"] += int(bd.es_si(conv["calificada"]))

    pipeline: Dict[str, int] = defaultdict(int)
    valor_pipeline = 0.0
    hasta_fin = [c for c in conversaciones if bd.fecha(c["fecha"]) <= fin]
    for conv in hasta_fin:
        etapa = conv["etapa"] or "nuevo"
        pipeline[etapa] += 1
        if etapa not in ("ganado", "perdido"):
            valor_pipeline += bd.numero(conv["valor_estimado_mxn"])

    # Sin acentos: DIAGNÓSTICO (bloque 1) y diagnostico cuentan juntas como DIAGNOSTICO.
    palabras: Dict[str, int] = defaultdict(int)
    for conv in de_semana:
        palabra = bd.normalizar(conv["palabra_clave"]).upper()
        if palabra:
            palabras[palabra] += 1

    return {
        "semana": {
            "conversaciones": len(de_semana),
            "calificadas": sum(1 for c in de_semana if bd.es_si(c["calificada"])),
            "diagnosticos": len(en_semana("diagnostico")),
            "propuestas": len(en_semana("propuesta")),
            "ganados": len(ganadas),
            "valor_ganado_mxn": sum(bd.numero(c["valor_cerrado_mxn"]) for c in ganadas),
        },
        "por_canal": dict(por_canal),
        "palabras_clave": dict(sorted(palabras.items(), key=lambda kv: -kv[1])),
        "pipeline": dict(pipeline),
        "valor_pipeline_mxn": valor_pipeline,
        "calificadas_totales": sum(1 for c in hasta_fin if bd.es_si(c["calificada"])),
        "conversaciones_totales": len(hasta_fin),
    }


def _contenido(publicaciones, semana, ventana_dias: int) -> Dict[str, Any]:
    fin = semana + dt.timedelta(days=6)
    desde = fin - dt.timedelta(days=ventana_dias - 1)
    piezas_semana = {(bd.fecha(p["fecha"]), bd.normalizar(p["tema"]))
                     for p in publicaciones if semana <= bd.fecha(p["fecha"]) <= fin}
    semanas_contenido = {bd.lunes(bd.fecha(p["fecha"])) for p in publicaciones if bd.fecha(p["fecha"]) <= fin}

    temas: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for pub in publicaciones:
        dia = bd.fecha(pub["fecha"])
        if not desde <= dia <= fin:
            continue
        tema = pub["tema"].strip() or "(sin tema)"
        for campo in ("alcance", "interacciones", "guardados", "compartidos",
                      "mensajes_palabra_clave", "clics_enlace"):
            temas[tema][campo] += bd.numero(pub[campo])
        temas[tema]["piezas"] += 1

    ranking = []
    for tema, valores in temas.items():
        if valores["alcance"] <= 0:
            continue
        fuertes = valores["guardados"] + valores["compartidos"] + valores["mensajes_palabra_clave"]
        ranking.append({
            "tema": tema,
            "alcance": valores["alcance"],
            "senales_fuertes": fuertes,
            "mensajes_palabra_clave": valores["mensajes_palabra_clave"],
            "tasa_senal": round(fuertes / valores["alcance"], 4),
            "tasa_interaccion": round(valores["interacciones"] / valores["alcance"], 4),
        })
    ranking.sort(key=lambda r: (-r["tasa_senal"], -r["mensajes_palabra_clave"], -r["alcance"]))
    suficiente = len(ranking) >= 3
    tercio = max(1, len(ranking) // 3) if suficiente else 0
    return {
        "publicaciones_semana": len(piezas_semana),
        "semanas_con_contenido": len(semanas_contenido),
        "ventana": [desde.isoformat(), fin.isoformat()],
        "suficiente": suficiente,
        "ranking": ranking,
        "repetir": [r["tema"] for r in ranking[:tercio]],
        "revisar": [r["tema"] for r in ranking[-tercio:]] if suficiente else [],
    }


def calcular(directorio: Path, semana: dt.date, config: Dict[str, Any]) -> Dict[str, Any]:
    """Construye el diccionario de KPI de la semana que empieza en `semana`."""
    semana = bd.lunes(semana)
    previa = semana - dt.timedelta(days=7)
    datos = bd.cargar_datos(directorio)
    bd.validar_datos(datos)  # DatosInvalidos (ValueError) con '<archivo> fila <n>: …'
    reglas = config["reglas"]

    canales, agrupado = _metricas_por_canal(datos["metricas"], semana, previa)
    pagados = {c: _historial_pagado(c, agrupado, datos["conversaciones"], semana)
               for c in bd.CANALES_PAGADOS}
    embudo = _embudo(datos["conversaciones"], semana)
    contenido = _contenido(datos["publicaciones"], semana, reglas["ventana_contenido_dias"])

    prospeccion_semana = canales.get("prospeccion", {}).get("semana", {})
    contactos_semana = prospeccion_semana.get("contactos_enviados", 0.0)
    respuestas_semana = prospeccion_semana.get("mensajes", 0.0)
    contactos_acumulados = sum(
        _sumar(filas)["contactos_enviados"]
        for lunes_semana, filas in agrupado.get("prospeccion", {}).items() if lunes_semana <= semana)

    metas_cfg = config["metas_semanales"]
    tasa_respuesta = round(respuestas_semana / contactos_semana, 4) if contactos_semana else None
    metas = [
        ("publicaciones", metas_cfg["publicaciones"], contenido["publicaciones_semana"]),
        ("contactos_personalizados", metas_cfg["contactos_personalizados"], contactos_semana),
        ("tasa_respuesta_prospeccion", metas_cfg["tasa_respuesta_prospeccion"], tasa_respuesta),
        ("conversaciones_calificadas", metas_cfg["conversaciones_calificadas"], embudo["semana"]["calificadas"]),
        ("diagnosticos", metas_cfg["diagnosticos"], embudo["semana"]["diagnosticos"]),
        ("propuestas", metas_cfg["propuestas"], embudo["semana"]["propuestas"]),
    ]

    faltantes = []
    for red in config["redes"]:
        if not canales.get(red, {}).get("con_datos"):
            faltantes.append(f"Sin métricas de {red} para la semana: extraerlas de Metricool o capturarlas a mano.")
    if not datos["conversaciones"]:
        faltantes.append("conversaciones.csv está vacío: registrar cada conversación de WhatsApp o mensaje directo.")
    if not datos["publicaciones"]:
        faltantes.append("publicaciones.csv está vacío: sin datos por publicación no se puede elegir qué temas repetir.")
    for canal, info in pagados.items():
        if info["inversion_acumulada"] > 0 and not canales.get(canal, {}).get("con_datos"):
            faltantes.append(f"{canal} tiene inversión previa pero no hay datos de esta semana.")

    return {
        "semana_inicio": semana.isoformat(),
        "semana_fin": (semana + dt.timedelta(days=6)).isoformat(),
        "canales": canales,
        "pagados": pagados,
        "embudo": embudo,
        "contenido": contenido,
        "prospeccion": {
            "contactos_semana": contactos_semana,
            "respuestas_semana": respuestas_semana,
            "tasa_respuesta": tasa_respuesta,
            "contactos_acumulados": contactos_acumulados,
        },
        "metas": [
            {"indicador": nombre, "meta": meta, "real": real,
             "cumple": None if real is None else real >= meta}
            for nombre, meta, real in metas
        ],
        "datos_faltantes": faltantes,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--semana", help="Cualquier fecha de la semana a reportar (AAAA-MM-DD)")
    parser.add_argument("--datos", type=Path, default=None, help="Directorio con los CSV")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--salida", type=Path, default=None, help="Archivo JSON de salida")
    args = parser.parse_args(argv)
    bd.preparar_consola()

    try:
        semana = bd.fecha(args.semana) if args.semana else bd.semana_reporte()
        resultado = calcular(args.datos or bd.datos_por_defecto(), semana, bd.cargar_config(args.config))
    except ValueError as error:
        print(f"Error en los datos:\n{error}", file=sys.stderr)
        return 2
    texto = json.dumps(resultado, ensure_ascii=False, indent=2)
    if args.salida:
        args.salida.write_text(texto + "\n", encoding="utf-8")
    else:
        print(texto)
    return 0


if __name__ == "__main__":
    sys.exit(main())

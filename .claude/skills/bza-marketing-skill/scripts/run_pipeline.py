#!/usr/bin/env python3
"""Ciclo semanal completo: KPI -> decisión Google vs Meta -> reporte Markdown.

Uso:
    python3 run_pipeline.py [--semana AAAA-MM-DD] [--datos DIR] [--reportes DIR]

Escribe `<reportes>/<lunes>.json` (KPI + decisión) y `<reportes>/<lunes>.md`.
Sin `--semana` reporta la última semana completa (hora de Ciudad de México).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

import bza_datos as bd
import decidir
import kpis as kpis_mod
import reporte


def ejecutar(datos: Path, reportes: Path, semana, config_path: Optional[Path] = None) -> dict:
    config = bd.cargar_config(config_path)
    resultado_kpis = kpis_mod.calcular(datos, semana, config)
    resultado_decision = decidir.decidir(resultado_kpis, config)
    texto = reporte.generar(resultado_kpis, resultado_decision)

    reportes.mkdir(parents=True, exist_ok=True)
    base = reportes / resultado_kpis["semana_inicio"]
    base.with_suffix(".json").write_text(
        json.dumps({"kpis": resultado_kpis, "decision": resultado_decision}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    base.with_suffix(".md").write_text(texto, encoding="utf-8")
    return {"kpis": resultado_kpis, "decision": resultado_decision,
            "markdown": str(base.with_suffix(".md")), "json": str(base.with_suffix(".json"))}


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--semana", help="Cualquier fecha de la semana a reportar (AAAA-MM-DD)")
    parser.add_argument("--datos", type=Path, default=None)
    parser.add_argument("--reportes", type=Path, default=None)
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args(argv)

    semana = bd.fecha(args.semana) if args.semana else bd.semana_reporte()
    datos = args.datos or bd.datos_por_defecto()
    reportes = args.reportes or bd.raiz_repo() / "marketing" / "reportes"
    try:
        salida = ejecutar(datos, reportes, semana, args.config)
    except ValueError as error:
        print(f"Error en los datos: {error}", file=sys.stderr)
        return 2
    decision = salida["decision"]
    print(f"Reporte: {salida['markdown']}")
    print(f"Estado de inversión: {decision['estado']}; reparto sugerido: "
          + ", ".join(f"{c} {v * 100:.0f}%" for c, v in decision["reparto_sugerido"].items()))
    print(f"Alertas: {len(decision['alertas'])}; acciones: {len(decision['acciones'])}; "
          f"datos faltantes: {len(decision['datos_faltantes'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

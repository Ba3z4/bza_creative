#!/usr/bin/env python3
"""Ejecuta los casos dorados de `evals/casos/` y reporta PASA/FALLA.

Uso:
    python3 run_evals.py            # todos los casos
    python3 run_evals.py reasignar  # solo los casos cuyo nombre contiene el texto
    python3 run_evals.py --validate # solo comprueba que los casos estén bien formados

Cada caso tiene `caso.json`:
- tipo "pipeline": `datos/` con los tres CSV, `semana`, `esperado` (subconjunto de
  {"kpis", "decision"}) y opcionalmente `alertas_contienen` / `acciones_contienen`.
- tipo "calendario": `bloque`, `valido` y opcionalmente `errores_contienen` / `avisos_contienen`.
"""
from __future__ import annotations

import json
import math
import sys
import tempfile
from pathlib import Path
from typing import Any, List

import bza_datos as bd
import calendario
import run_pipeline

CASOS = bd.SKILL_DIR / "evals" / "casos"


def subconjunto(esperado: Any, real: Any, ruta: str, fallas: List[str]) -> None:
    if isinstance(esperado, dict):
        if not isinstance(real, dict):
            fallas.append(f"{ruta}: se esperaba objeto, llegó {real!r}")
            return
        for clave, valor in esperado.items():
            if clave not in real:
                fallas.append(f"{ruta}.{clave}: falta")
            else:
                subconjunto(valor, real[clave], f"{ruta}.{clave}", fallas)
    elif isinstance(esperado, float) or (isinstance(esperado, int) and isinstance(real, float)):
        if not isinstance(real, (int, float)) or not math.isclose(esperado, real, abs_tol=0.01):
            fallas.append(f"{ruta}: esperado {esperado}, real {real}")
    elif esperado != real:
        fallas.append(f"{ruta}: esperado {esperado!r}, real {real!r}")


def contiene(textos: List[str], fragmentos: List[str], etiqueta: str, fallas: List[str]) -> None:
    for fragmento in fragmentos:
        if not any(fragmento in texto for texto in textos):
            fallas.append(f"{etiqueta}: ninguna contiene {fragmento!r}")


def correr_caso(directorio: Path) -> List[str]:
    caso = json.loads((directorio / "caso.json").read_text(encoding="utf-8"))
    fallas: List[str] = []
    if caso["tipo"] == "pipeline":
        with tempfile.TemporaryDirectory() as temporal:
            salida = run_pipeline.ejecutar(directorio / "datos", Path(temporal), bd.fecha(caso["semana"]))
            markdown = Path(salida["markdown"]).read_text(encoding="utf-8")
        if not markdown.startswith("# Reporte semanal BZA Creative"):
            fallas.append("reporte: encabezado inesperado")
        subconjunto(caso.get("esperado", {}), {"kpis": salida["kpis"], "decision": salida["decision"]}, "$", fallas)
        contiene(salida["decision"]["alertas"], caso.get("alertas_contienen", []), "alertas", fallas)
        contiene([a["texto"] for a in salida["decision"]["acciones"]], caso.get("acciones_contienen", []), "acciones", fallas)
    elif caso["tipo"] == "calendario":
        bloque = calendario.cargar(directorio / caso["bloque"])
        errores, avisos = calendario.validar(bloque, bd.cargar_config(), bd.raiz_repo(bd.SKILL_DIR))
        if (not errores) != caso["valido"]:
            fallas.append(f"válido={not errores}, esperado {caso['valido']}; errores: {errores}")
        contiene(errores, caso.get("errores_contienen", []), "errores", fallas)
        contiene(avisos, caso.get("avisos_contienen", []), "avisos", fallas)
        if caso["valido"] and not errores:
            calendario.markdown(bloque, bd.cargar_config())
            cargas = calendario.cargas_metricool(bloque, bd.cargar_config(), publicar=False)
            if not all(c["draft"] for c in cargas):
                fallas.append("las cargas para Metricool deben ser borrador por defecto")
    else:
        fallas.append(f"tipo desconocido {caso['tipo']!r}")
    return fallas


def validar_casos(directorios: List[Path]) -> int:
    problemas = 0
    for directorio in directorios:
        try:
            caso = json.loads((directorio / "caso.json").read_text(encoding="utf-8"))
            assert caso.get("tipo") in {"pipeline", "calendario"}, "tipo inválido"
            if caso["tipo"] == "pipeline":
                assert (directorio / "datos").is_dir() and caso.get("semana"), "faltan datos o semana"
            else:
                assert (directorio / caso["bloque"]).is_file() and "valido" in caso, "falta bloque o valido"
        except (OSError, ValueError, AssertionError, KeyError) as error:
            problemas += 1
            print(f"INVÁLIDO {directorio.name}: {error}")
    print("VALID" if not problemas else f"{problemas} casos inválidos")
    return 1 if problemas else 0


def main(argv: List[str]) -> int:
    filtro = [a for a in argv if not a.startswith("--")]
    directorios = sorted(d for d in CASOS.iterdir() if (d / "caso.json").exists()
                         and (not filtro or any(f in d.name for f in filtro)))
    if "--validate" in argv:
        return validar_casos(directorios)
    total_fallas = 0
    for directorio in directorios:
        fallas = correr_caso(directorio)
        total_fallas += bool(fallas)
        print(f"{'PASA ' if not fallas else 'FALLA'} {directorio.name}")
        for falla in fallas:
            print(f"      - {falla}")
    print(f"\n{len(directorios) - total_fallas}/{len(directorios)} casos pasan")
    return 1 if total_fallas else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

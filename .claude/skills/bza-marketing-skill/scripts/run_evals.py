#!/usr/bin/env python3
"""Ejecuta los casos dorados de `evals/casos/` y reporta PASA/FALLA.

Uso:
    python3 run_evals.py            # todos los casos
    python3 run_evals.py reasignar  # solo los casos cuyo nombre contiene el texto
    python3 run_evals.py --validate # solo comprueba que los casos estén bien formados

Cada caso tiene `caso.json`:
- tipo "pipeline": `datos/` con los tres CSV, `semana`, `esperado` (subconjunto de
  {"kpis", "decision"}) y opcionalmente `alertas_contienen`, `acciones_contienen`,
  `acciones_no_contienen`, `reporte_contiene` y `config` (claves de primer nivel que
  reemplazan a las de `assets/config.json` solo en ese caso, p. ej. `pendientes_fase0`).
- tipo "calendario": `bloque`, `valido` y opcionalmente `errores_contienen` / `avisos_contienen`.
  Si el bloque es válido, también se genera la vista previa HTML (sin escribirla) y se
  comprueba que tenga `noindex`, que cada `src` sea relativo y apunte a un archivo de
  `dist/`, y que contenga los fragmentos de `preview_contiene`.
"""
from __future__ import annotations

import html
import json
import math
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, List
from urllib.parse import unquote

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


def revisar_preview(pagina: str, salida: Path, dist: Path, fragmentos: List[str], fallas: List[str]) -> None:
    """La vista previa no se indexa y todas sus piezas son rutas relativas que existen en dist/."""
    if '<meta name="robots" content="noindex,nofollow">' not in pagina:
        fallas.append("preview: falta <meta name=\"robots\" content=\"noindex,nofollow\">")
    fuentes = [html.unescape(v) for v in re.findall(r'\b(?:src|poster)="([^"]+)"', pagina)]
    if not fuentes:
        fallas.append("preview: no hay medios")
    for fuente in fuentes:
        if re.match(r"^(?:[a-z]+:|/)", fuente):
            fallas.append(f"preview: {fuente} no es una ruta relativa")
            continue
        destino = (salida.parent / unquote(fuente)).resolve()
        if not destino.is_relative_to(dist) or not destino.is_file():
            fallas.append(f"preview: {fuente} no apunta a un archivo dentro de dist/")
    for fragmento in fragmentos:
        if fragmento not in pagina:
            fallas.append(f"preview: no contiene {fragmento!r}")


def correr_caso(directorio: Path) -> List[str]:
    caso = json.loads((directorio / "caso.json").read_text(encoding="utf-8"))
    fallas: List[str] = []
    if caso["tipo"] == "pipeline":
        with tempfile.TemporaryDirectory() as temporal:
            config_path = None
            if caso.get("config"):
                config_path = Path(temporal) / "config.json"
                config_path.write_text(json.dumps({**bd.cargar_config(), **caso["config"]}, ensure_ascii=False),
                                       encoding="utf-8")
            salida = run_pipeline.ejecutar(directorio / "datos", Path(temporal) / "reportes",
                                           bd.fecha(caso["semana"]), config_path)
            markdown = Path(salida["markdown"]).read_text(encoding="utf-8")
        if not markdown.startswith("# Reporte semanal BZA Creative"):
            fallas.append("reporte: encabezado inesperado")
        subconjunto(caso.get("esperado", {}), {"kpis": salida["kpis"], "decision": salida["decision"]}, "$", fallas)
        contiene(salida["decision"]["alertas"], caso.get("alertas_contienen", []), "alertas", fallas)
        acciones = [a["texto"] for a in salida["decision"]["acciones"]]
        contiene(acciones, caso.get("acciones_contienen", []), "acciones", fallas)
        for fragmento in caso.get("acciones_no_contienen", []):
            if any(fragmento in texto for texto in acciones):
                fallas.append(f"acciones: ninguna debería contener {fragmento!r}")
        contiene([markdown], caso.get("reporte_contiene", []), "reporte", fallas)
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
            raiz = bd.raiz_repo(bd.SKILL_DIR)
            dist = (raiz / "dist").resolve()
            # Ruta virtual: la página no se escribe, solo se calcula como si viviera en dist/.
            salida = dist / "campana-preview" / directorio.name / "index.html"
            pagina = calendario.preview(bloque, bd.cargar_config(), salida, raiz, avisos)
            revisar_preview(pagina, salida, dist, caso.get("preview_contiene", []), fallas)
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

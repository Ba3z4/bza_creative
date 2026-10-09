#!/usr/bin/env python3
"""Ejecuta los casos dorados de `evals/casos/` y reporta PASA/FALLA.

Uso:
    python3 run_evals.py            # todos los casos
    python3 run_evals.py reasignar  # solo los casos cuyo nombre contiene el texto
    python3 run_evals.py --validate # solo comprueba que los casos estén bien formados

Cada caso tiene `caso.json`:
- tipo "pipeline": `datos/` con los tres CSV, `semana`, `esperado` (subconjunto de
  {"kpis", "decision"}; los números se comparan con tolerancia de 0.001) y opcionalmente
  `alertas_contienen`, `acciones_contienen`, `acciones_no_contienen`, `reporte_contiene`,
  `otras_semanas` (lista de objetos con su propia `semana` y las mismas claves, sobre los
  mismos datos) y `config` (se combina con `assets/config.json` solo en ese caso; los
  objetos se combinan clave por clave y las listas se reemplazan).
  Con `error_contiene`, el caso espera que `run_pipeline.py` termine con código 2 y que
  stderr contenga cada fragmento (archivo y fila del dato inválido).
- tipo "calendario": `bloque`, `valido` y opcionalmente `errores_contienen` / `avisos_contienen`.
  Si el bloque es válido, también:
  - genera las cargas de Metricool con `calendario.py metricool` (CLI) y comprueba que
    sean borrador, que cada medio sea una URL absoluta `https://bzacreative.com/assets/...`,
    que las publicaciones de `cargas_excluidas` (piezas PENDIENTE) no tengan carga y se
    avisen en stderr, y que `cargas_medios` ({id: [urls]}) coincida;
  - genera la vista previa HTML (sin escribirla) y comprueba que tenga `noindex`, que cada
    `src` sea relativo y apunte a un archivo de `dist/`, que contenga los fragmentos de
    `preview_contiene` y ninguno de `preview_no_contiene`.
"""
from __future__ import annotations

import contextlib
import html
import io
import json
import math
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import unquote

import bza_datos as bd
import calendario
import run_pipeline

CASOS = bd.SKILL_DIR / "evals" / "casos"
TOLERANCIA = 1e-3  # repartos con 3 decimales: 0.904 no pasa por 0.90
CLAVES_SEMANA = {"semana", "esperado", "alertas_contienen", "acciones_contienen", "acciones_no_contienen",
                 "reporte_contiene"}


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
        if not isinstance(real, (int, float)) or not math.isclose(esperado, real, abs_tol=TOLERANCIA):
            fallas.append(f"{ruta}: esperado {esperado}, real {real}")
    elif esperado != real:
        fallas.append(f"{ruta}: esperado {esperado!r}, real {real!r}")


def contiene(textos: List[str], fragmentos: List[str], etiqueta: str, fallas: List[str]) -> None:
    for fragmento in fragmentos:
        if not any(fragmento in texto for texto in textos):
            fallas.append(f"{etiqueta}: ninguna contiene {fragmento!r}")


def combinar(base: Dict[str, Any], cambios: Dict[str, Any]) -> Dict[str, Any]:
    """Combina `cambios` sobre `base`: objetos clave por clave, listas y valores reemplazados."""
    resultado = dict(base)
    for clave, valor in cambios.items():
        if isinstance(valor, dict) and isinstance(resultado.get(clave), dict):
            resultado[clave] = combinar(resultado[clave], valor)
        else:
            resultado[clave] = valor
    return resultado


def revisar_preview(pagina: str, salida: Path, dist: Path, caso: Dict[str, Any], fallas: List[str]) -> None:
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
        if not bd.dentro_de(destino, dist) or not destino.is_file():
            fallas.append(f"preview: {fuente} no apunta a un archivo dentro de dist/")
    for fragmento in caso.get("preview_contiene", []):
        if fragmento not in pagina:
            fallas.append(f"preview: no contiene {fragmento!r}")
    for fragmento in caso.get("preview_no_contiene", []):
        if fragmento in pagina:
            fallas.append(f"preview: no debería contener {fragmento!r}")


def revisar_cargas(ruta_bloque: Path, caso: Dict[str, Any], config: Dict[str, Any], fallas: List[str]) -> None:
    """Corre `calendario.py metricool` como lo haría el agente y revisa el JSON y stderr."""
    with tempfile.TemporaryDirectory() as temporal:
        salida = Path(temporal) / "cargas.json"
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            codigo = calendario.main(["metricool", str(ruta_bloque), "--salida", str(salida)])
        if codigo != 0 or not salida.is_file():
            fallas.append(f"metricool: código {codigo}; stderr: {stderr.getvalue()!r}")
            return
        cargas = json.loads(salida.read_text(encoding="utf-8"))
    errores = stderr.getvalue()
    if not all(c["draft"] for c in cargas):
        fallas.append("metricool: las cargas deben ser borrador por defecto")
    prefijo = config["assets_publicos"].rstrip("/") + "/assets/"
    for carga in cargas:
        for medio in carga["media"]:
            if not (medio.startswith("https://") and medio.startswith(prefijo)):
                fallas.append(f"metricool: {carga['id_bza']} tiene un medio que no es URL pública absoluta: {medio}")
        if not carga["media"]:
            fallas.append(f"metricool: {carga['id_bza']} no tiene medios")
    ids = [c["id_bza"] for c in cargas]
    for excluida in caso.get("cargas_excluidas", []):
        if excluida in ids:
            fallas.append(f"metricool: {excluida} tiene pieza pendiente y no debería tener carga")
        if f"EXCLUIDA  {excluida}" not in errores:
            fallas.append(f"metricool: stderr no avisa que {excluida} quedó excluida")
    for ref, medios in caso.get("cargas_medios", {}).items():
        reales = next((c["media"] for c in cargas if c["id_bza"] == ref), None)
        if reales != medios:
            fallas.append(f"metricool: medios de {ref}: esperado {medios}, real {reales}")
    for fragmento in caso.get("avisos_contienen", []):
        if fragmento not in errores:
            fallas.append(f"metricool: stderr no contiene el aviso {fragmento!r}")


def revisar_semana(caso: Dict[str, Any], datos: Path, config_path: Any, etiqueta: str, fallas: List[str]) -> None:
    with tempfile.TemporaryDirectory() as temporal:
        salida = run_pipeline.ejecutar(datos, Path(temporal) / "reportes", bd.fecha(caso["semana"]), config_path)
        markdown = Path(salida["markdown"]).read_text(encoding="utf-8")
    propias: List[str] = []
    if not markdown.startswith("# Reporte semanal BZA Creative"):
        propias.append("reporte: encabezado inesperado")
    subconjunto(caso.get("esperado", {}), {"kpis": salida["kpis"], "decision": salida["decision"]}, "$", propias)
    contiene(salida["decision"]["alertas"], caso.get("alertas_contienen", []), "alertas", propias)
    acciones = [a["texto"] for a in salida["decision"]["acciones"]]
    contiene(acciones, caso.get("acciones_contienen", []), "acciones", propias)
    for fragmento in caso.get("acciones_no_contienen", []):
        if any(fragmento in texto for texto in acciones):
            propias.append(f"acciones: ninguna debería contener {fragmento!r}")
    contiene([markdown], caso.get("reporte_contiene", []), "reporte", propias)
    fallas.extend(f"{etiqueta}{falla}" for falla in propias)


def correr_pipeline(directorio: Path, caso: Dict[str, Any], fallas: List[str]) -> None:
    with tempfile.TemporaryDirectory() as temporal:
        config_path = None
        if caso.get("config"):
            config_path = Path(temporal) / "config.json"
            config_path.write_text(json.dumps(combinar(bd.cargar_config(), caso["config"]), ensure_ascii=False),
                                   encoding="utf-8")
        if caso.get("error_contiene"):
            argumentos = ["--semana", caso["semana"], "--datos", str(directorio / "datos"),
                          "--reportes", str(Path(temporal) / "reportes")]
            if config_path:
                argumentos += ["--config", str(config_path)]
            stdout, stderr = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                codigo = run_pipeline.main(argumentos)
            if codigo != 2:
                fallas.append(f"run_pipeline terminó con código {codigo}, se esperaba 2")
            contiene([stderr.getvalue()], caso["error_contiene"], "stderr", fallas)
            return
        revisar_semana(caso, directorio / "datos", config_path, "", fallas)
        for otra in caso.get("otras_semanas", []):
            revisar_semana(otra, directorio / "datos", config_path, f"[{otra['semana']}] ", fallas)


def correr_calendario(directorio: Path, caso: Dict[str, Any], fallas: List[str]) -> None:
    config = bd.cargar_config()
    ruta_bloque = directorio / caso["bloque"]
    bloque = calendario.cargar(ruta_bloque)
    raiz = bd.raiz_repo(bd.SKILL_DIR)
    errores, avisos = calendario.validar(bloque, config, raiz)
    if (not errores) != caso["valido"]:
        fallas.append(f"válido={not errores}, esperado {caso['valido']}; errores: {errores}")
    contiene(errores, caso.get("errores_contienen", []), "errores", fallas)
    contiene(avisos, caso.get("avisos_contienen", []), "avisos", fallas)
    if caso["valido"] and not errores:
        calendario.markdown(bloque, config)
        revisar_cargas(ruta_bloque, caso, config, fallas)
        dist = (raiz / "dist").resolve()
        # Ruta virtual: la página no se escribe, solo se calcula como si viviera en dist/.
        salida = dist / "campana-preview" / directorio.name / "index.html"
        pagina = calendario.preview(bloque, config, salida, raiz, avisos)
        revisar_preview(pagina, salida, dist, caso, fallas)


def correr_caso(directorio: Path) -> List[str]:
    caso = json.loads((directorio / "caso.json").read_text(encoding="utf-8"))
    fallas: List[str] = []
    try:
        if caso["tipo"] == "pipeline":
            correr_pipeline(directorio, caso, fallas)
        elif caso["tipo"] == "calendario":
            correr_calendario(directorio, caso, fallas)
        else:
            fallas.append(f"tipo desconocido {caso['tipo']!r}")
    except (ValueError, KeyError, OSError) as error:
        fallas.append(f"error inesperado: {type(error).__name__}: {error}")
    return fallas


def validar_casos(directorios: List[Path]) -> int:
    problemas = 0
    for directorio in directorios:
        try:
            caso = json.loads((directorio / "caso.json").read_text(encoding="utf-8"))
            assert caso.get("tipo") in {"pipeline", "calendario"}, "tipo inválido"
            assert caso.get("descripcion"), "falta descripcion"
            if caso["tipo"] == "pipeline":
                assert (directorio / "datos").is_dir() and caso.get("semana"), "faltan datos o semana"
                bd.fecha(caso["semana"])
                assert isinstance(caso.get("config", {}), dict), "config debe ser objeto"
                assert isinstance(caso.get("error_contiene", []), list), "error_contiene debe ser lista"
                for otra in caso.get("otras_semanas", []):
                    bd.fecha(otra["semana"])
                    sobrantes = set(otra) - CLAVES_SEMANA
                    assert not sobrantes, f"otras_semanas: claves desconocidas {sorted(sobrantes)}"
                tiene_comprobacion = any(caso.get(k) for k in CLAVES_SEMANA - {"semana"} | {"error_contiene"})
                assert tiene_comprobacion, "el caso no comprueba nada"
            else:
                assert (directorio / caso["bloque"]).is_file() and "valido" in caso, "falta bloque o valido"
                assert isinstance(caso.get("cargas_medios", {}), dict), "cargas_medios debe ser objeto"
        except (OSError, ValueError, AssertionError, KeyError, TypeError) as error:
            problemas += 1
            print(f"INVÁLIDO {directorio.name}: {error}")
    print(f"VALID: {len(directorios)} casos" if not problemas else f"{problemas} casos inválidos")
    return 1 if problemas else 0


def main(argv: List[str]) -> int:
    bd.preparar_consola()
    filtro = [a for a in argv if not a.startswith("--")]
    directorios = sorted(d for d in CASOS.iterdir() if (d / "caso.json").exists()
                         and (not filtro or any(f in d.name for f in filtro)))
    if not directorios:
        print(f"Ningún caso coincide con {filtro}")
        return 1
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

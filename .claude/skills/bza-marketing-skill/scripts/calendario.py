#!/usr/bin/env python3
"""Valida un bloque de contenido y lo convierte a Markdown o a cargas para Metricool.

Uso:
    python3 calendario.py validar  marketing/calendario/bloque-02.json
    python3 calendario.py markdown marketing/calendario/bloque-02.json [--salida docs/x.md]
    python3 calendario.py metricool marketing/calendario/bloque-02.json [--publicar] [--salida x.json]

`validar` termina con código 1 si hay errores. `metricool` solo genera las
cargas si el bloque es válido; por defecto las marca como borrador.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

import bza_datos as bd

CAMPOS = ("id", "fecha", "redes", "formato", "tema", "palabra_clave", "piezas", "texto", "utm_content")
FORMATOS = {"imagen": 1, "carrusel": 2, "reel": 1}
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def cargar(ruta: Path) -> Dict[str, Any]:
    return json.loads(ruta.read_text(encoding="utf-8"))


def enlace(bloque: Dict[str, Any], pub: Dict[str, Any], red: str, config: Dict[str, Any]) -> str:
    parametros = {
        "utm_source": red,
        "utm_medium": "organic_social",
        "utm_campaign": bloque.get("utm_campaign", config["utm_campaign_organico"]),
        "utm_content": pub["utm_content"],
    }
    return f"{config['landing']}?{urlencode(parametros)}"


def validar(bloque: Dict[str, Any], config: Dict[str, Any], raiz: Path) -> Tuple[List[str], List[str]]:
    """Devuelve (errores, avisos)."""
    errores: List[str] = []
    avisos: List[str] = []
    reglas = config["publicacion"]
    try:
        inicio, fin = bd.fecha(bloque["inicio"]), bd.fecha(bloque["fin"])
    except (KeyError, ValueError) as error:
        return [f"bloque: inicio/fin inválidos ({error})"], []

    vistos = set()
    usos_palabra: Dict[str, List[dt.date]] = defaultdict(list)
    por_dia: Dict[dt.date, int] = defaultdict(int)
    por_semana: Dict[dt.date, int] = defaultdict(int)
    for indice, pub in enumerate(bloque.get("publicaciones", []), start=1):
        ref = pub.get("id") or f"#{indice}"
        faltan = [c for c in CAMPOS if not pub.get(c)]
        if faltan:
            errores.append(f"{ref}: faltan campos {', '.join(faltan)}")
            continue
        if ref in vistos:
            errores.append(f"{ref}: id repetido")
        vistos.add(ref)

        try:
            momento = dt.datetime.fromisoformat(pub["fecha"])
        except ValueError:
            errores.append(f"{ref}: fecha inválida {pub['fecha']!r} (usar AAAA-MM-DDTHH:MM)")
            continue
        dia = momento.date()
        if not inicio <= dia <= fin:
            errores.append(f"{ref}: {dia} está fuera del bloque {inicio} – {fin}")
        por_dia[dia] += 1
        por_semana[bd.lunes(dia)] += 1
        hora = momento.strftime("%H:%M")
        esperado = reglas["hora_reel"] if pub["formato"] == "reel" else reglas["hora_publicacion"]
        if hora != esperado:
            avisos.append(f"{ref}: hora {hora}; la ventana habitual es {esperado}")

        redes_invalidas = set(pub["redes"]) - set(config["redes"])
        if redes_invalidas:
            errores.append(f"{ref}: redes no configuradas {sorted(redes_invalidas)}")

        formato = pub["formato"]
        if formato not in FORMATOS:
            errores.append(f"{ref}: formato {formato!r} no es imagen, carrusel ni reel")
        elif len(pub["piezas"]) < FORMATOS[formato]:
            errores.append(f"{ref}: {formato} necesita al menos {FORMATOS[formato]} pieza(s)")
        for pieza in pub["piezas"]:
            if pieza.startswith("PENDIENTE:"):
                avisos.append(f"{ref}: pieza pendiente de producir — {pieza[10:].strip()}")
                continue
            ruta = raiz / pieza
            if not pieza.startswith("dist/"):
                errores.append(f"{ref}: {pieza} debe estar dentro de dist/ para tener URL pública")
            elif not ruta.is_file():
                errores.append(f"{ref}: no existe {pieza}")
            if formato == "reel" and not pieza.endswith(".mp4"):
                errores.append(f"{ref}: un reel necesita un .mp4, no {pieza}")

        palabra = pub["palabra_clave"]
        if not re.fullmatch(r"[A-Z0-9]{3,15}", palabra):
            errores.append(f"{ref}: palabra clave {palabra!r} debe ir en MAYÚSCULAS sin acentos ni espacios")
        if palabra not in pub["texto"]:
            errores.append(f"{ref}: el texto no menciona la palabra clave {palabra}")
        usos_palabra[palabra].append(dia)

        texto = pub["texto"]
        if len(texto) > reglas["max_caracteres"]:
            errores.append(f"{ref}: texto de {len(texto)} caracteres (máximo {reglas['max_caracteres']})")
        hashtags = re.findall(r"#\w+", texto)
        if len(hashtags) > reglas["max_hashtags"]:
            errores.append(f"{ref}: {len(hashtags)} hashtags (máximo {reglas['max_hashtags']})")
        if re.search(r"https?://", texto):
            avisos.append(f"{ref}: Instagram no vuelve clicable un enlace en el texto; usar el enlace del perfil")
        if not re.fullmatch(r"[a-z0-9_]+", pub["utm_content"]):
            errores.append(f"{ref}: utm_content {pub['utm_content']!r} debe ir en minúsculas, números y guion bajo")

    for palabra, dias in usos_palabra.items():
        dias.sort()
        for anterior, siguiente in zip(dias, dias[1:]):
            if (siguiente - anterior).days < reglas["dias_sin_repetir_palabra"]:
                errores.append(f"palabra clave {palabra} repetida en {anterior} y {siguiente}: "
                               f"separar al menos {reglas['dias_sin_repetir_palabra']} días")
    for dia, cantidad in sorted(por_dia.items()):
        if cantidad > 1:
            avisos.append(f"{dia}: {cantidad} publicaciones el mismo día")
    for semana in bd.semanas(inicio, fin):
        cantidad = por_semana.get(semana, 0)
        if cantidad < config["metas_semanales"]["publicaciones"]:
            avisos.append(f"semana del {semana}: {cantidad} publicaciones "
                          f"(meta {config['metas_semanales']['publicaciones']})")
    if not bloque.get("publicaciones"):
        errores.append("el bloque no tiene publicaciones")
    return errores, avisos


def _fecha_larga(momento: dt.datetime) -> str:
    return f"{DIAS[momento.weekday()]} {momento.day} {MESES[momento.month - 1]}, {momento.strftime('%H:%M')}"


def markdown(bloque: Dict[str, Any], config: Dict[str, Any]) -> str:
    lineas = [f"# Calendario de contenido — {bloque.get('titulo', bloque['bloque'])}", ""]
    lineas.append(f"Periodo: {bloque['inicio']} a {bloque['fin']} · Zona horaria: `{config['zona_horaria']}`  ")
    lineas.append(f"Campaña UTM: `{bloque.get('utm_campaign', config['utm_campaign_organico'])}` · "
                  f"Redes: {', '.join(config['redes'])}")
    if bloque.get("objetivo"):
        lineas += ["", bloque["objetivo"]]
    lineas += ["", "| Fecha | Tema | Formato | Palabra | Pieza |", "|---|---|---|---|---|"]
    for pub in bloque["publicaciones"]:
        momento = dt.datetime.fromisoformat(pub["fecha"])
        pieza = Path(pub["piezas"][0]).name if not pub["piezas"][0].startswith("PENDIENTE:") else "pendiente"
        lineas.append(f"| {_fecha_larga(momento)} | {pub['tema']} | {pub['formato']} | "
                      f"`{pub['palabra_clave']}` | {pieza} |")
    lineas.append("")
    for pub in bloque["publicaciones"]:
        momento = dt.datetime.fromisoformat(pub["fecha"])
        lineas += [f"## {pub['id']} · {pub['tema']}", ""]
        lineas.append(f"- **Fecha:** {_fecha_larga(momento)}")
        lineas.append(f"- **Formato:** {pub['formato']} · **Palabra clave:** `{pub['palabra_clave']}`")
        lineas.append("- **Piezas:** " + ", ".join(f"`{p}`" for p in pub["piezas"]))
        lineas.append(f"- **Enlace para historia:** `{enlace(bloque, pub, 'instagram', config)}`")
        if pub.get("objetivo"):
            lineas.append(f"- **Objetivo:** {pub['objetivo']}")
        lineas += ["", "**Texto:**", ""]
        lineas += [f"> {linea}" if linea else ">" for linea in pub["texto"].split("\n")]
        if pub.get("historia"):
            lineas += ["", f"**Historia (17:00–18:00):** {pub['historia']}"]
        lineas.append("")
    return "\n".join(lineas)


def cargas_metricool(bloque: Dict[str, Any], config: Dict[str, Any], publicar: bool) -> List[Dict[str, Any]]:
    """Cargas en el formato de `createScheduledPost`. El agente debe ajustarlas al
    esquema real de la herramienta que exponga el conector (ver references/metricool.md)."""
    cargas = []
    for pub in bloque["publicaciones"]:
        momento = dt.datetime.fromisoformat(pub["fecha"])
        medios = [config["assets_publicos"] + p[len("dist/"):] for p in pub["piezas"] if p.startswith("dist/")]
        cargas.append({
            "id_bza": pub["id"],
            "publicationDate": {"dateTime": momento.strftime("%Y-%m-%dT%H:%M:%S"),
                                "timezone": config["zona_horaria"]},
            "text": pub["texto"],
            "providers": [{"network": red} for red in pub["redes"]],
            "media": medios,
            "formato": pub["formato"],
            "draft": not publicar,
            "enlaces_utm": {red: enlace(bloque, pub, red, config) for red in pub["redes"]},
        })
    return cargas


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("accion", choices=["validar", "markdown", "metricool"])
    parser.add_argument("bloque", type=Path)
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--raiz", type=Path, default=None, help="Raíz del repositorio (contiene dist/)")
    parser.add_argument("--salida", type=Path, default=None)
    parser.add_argument("--publicar", action="store_true", help="Marcar las cargas como publicación, no borrador")
    args = parser.parse_args(argv)

    config = bd.cargar_config(args.config)
    bloque = cargar(args.bloque)
    raiz = args.raiz or bd.raiz_repo(args.bloque.resolve().parent)
    errores, avisos = validar(bloque, config, raiz)

    if args.accion == "validar" or errores:
        for aviso in avisos:
            print(f"AVISO  {aviso}")
        for error in errores:
            print(f"ERROR  {error}")
        total = len(bloque.get("publicaciones", []))
        print(f"{'VÁLIDO' if not errores else 'INVÁLIDO'}: {total} publicaciones, "
              f"{len(errores)} errores, {len(avisos)} avisos")
        if args.accion == "validar" or errores:
            return 1 if errores else 0

    if args.accion == "markdown":
        salida = markdown(bloque, config)
    else:
        salida = json.dumps(cargas_metricool(bloque, config, args.publicar), ensure_ascii=False, indent=2)
    if args.salida:
        args.salida.write_text(salida + ("\n" if not salida.endswith("\n") else ""), encoding="utf-8")
        print(f"Escrito {args.salida}")
    else:
        print(salida)
    return 0


if __name__ == "__main__":
    sys.exit(main())

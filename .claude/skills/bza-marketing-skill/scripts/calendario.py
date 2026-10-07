#!/usr/bin/env python3
"""Valida un bloque de contenido y lo convierte a Markdown, a cargas para Metricool
o a una vista previa en HTML.

Uso:
    python3 calendario.py validar  marketing/calendario/bloque-02.json
    python3 calendario.py markdown marketing/calendario/bloque-02.json [--salida docs/x.md]
    python3 calendario.py metricool marketing/calendario/bloque-02.json [--publicar] [--salida x.json]
    python3 calendario.py preview  marketing/calendario/bloque-02.json [--salida ruta/index.html]

`validar` termina con código 1 si hay errores. `markdown`, `metricool` y `preview`
solo generan salida si el bloque es válido; las cargas de `metricool` salen como
borrador por defecto. `preview` escribe por defecto
`dist/campana-preview/<bloque>/index.html` (con `noindex`), con rutas relativas a
las piezas de `dist/` para que funcione en local y en el sitio desplegado.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote, urlencode

import bza_datos as bd

CAMPOS = ("id", "fecha", "redes", "formato", "tema", "palabra_clave", "piezas", "texto", "utm_content")
FORMATOS = {"imagen": 1, "carrusel": 2, "reel": 1}
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
DIAS_CORTOS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
NOMBRES_RED = {"facebook": "Facebook", "instagram": "Instagram"}
NOMBRES_FORMATO = {"imagen": "Imagen", "carrusel": "Carrusel", "reel": "Reel"}
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


# El mismo ícono del sitio, en línea para que la vista previa no dependa de otro archivo.
FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' "
           "height='64' rx='14' fill='%23df3023'/%3E%3Cpath d='M28 10h8v15l11-11 6 6-11 12h15v8H42l11 11-6 6-11-11v15h"
           "-8V46L17 57l-6-6 11-11H7v-8h15L11 20l6-6 11 11z' transform='translate(0 -4)' fill='white'/%3E%3C/svg%3E")

PREVIEW_CSS = """
:root{--ink:#151515;--muted:#5f5e58;--paper:#f4f1e9;--white:#fff;--green:#073f39;--green-soft:#e2ebe8;--red:#df3023;--line:#dedbd2;color-scheme:light}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.5 Arial,Helvetica,sans-serif;-webkit-text-size-adjust:100%}
a{color:inherit}
.wrap{width:min(1180px,calc(100% - 32px));margin:0 auto}
.top{position:sticky;top:0;z-index:5;background:rgba(244,241,233,.94);backdrop-filter:blur(14px);border-bottom:1px solid var(--line)}
.top .wrap{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:14px 0}
.brand{font-size:20px;font-weight:800;letter-spacing:-.04em;white-space:nowrap}
.brand::before{content:"\\2733";color:var(--red);margin-right:8px}
.top nav{display:flex;align-items:center;gap:18px;font-size:13px;font-weight:700}
.top nav a{text-decoration:none}
.top nav a:hover{color:var(--red)}
.badge{padding:7px 12px;border-radius:100px;background:var(--green);color:#fff;font-size:11px;font-weight:700;letter-spacing:.08em;white-space:nowrap}
@media (max-width:360px){.badge{font-size:9px;letter-spacing:.03em;padding:6px 8px}.brand{font-size:17px}}
.hero{display:grid;grid-template-columns:1.3fr .7fr;gap:48px;align-items:end;padding:60px 0 36px}
.eyebrow{margin:0;color:var(--red);font-size:12px;font-weight:800;letter-spacing:.16em;text-transform:uppercase}
h1{font-size:clamp(36px,5.6vw,72px);line-height:1;letter-spacing:-.05em;margin:16px 0 20px;overflow-wrap:anywhere}
.lead{max-width:680px;margin:0;color:var(--muted);font-size:18px;line-height:1.6}
.stats{display:grid;grid-template-columns:repeat(2,1fr);margin:0;border:1px solid var(--line);background:var(--white)}
.stats div{display:flex;flex-direction:column-reverse;justify-content:flex-end;padding:22px;border-bottom:1px solid var(--line)}
.stats div:nth-child(odd){border-right:1px solid var(--line)}
.stats div:nth-last-child(-n+2){border-bottom:0}
.stats dd{margin:0;font-size:38px;font-weight:800;line-height:1;color:var(--green);letter-spacing:-.03em}
.stats dt{margin-top:8px;font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.1em}
.resumen{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1px;margin:0;background:var(--line);border:1px solid var(--line)}
.resumen div{background:var(--white);padding:16px 18px;min-width:0}
.resumen dt,.campos dt{font-size:11px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.resumen dd{margin:6px 0 0;font-weight:700;overflow-wrap:anywhere}
.palabras{display:flex;flex-wrap:wrap;gap:8px;margin:0;padding:0;list-style:none}
.palabras a{display:inline-block;padding:6px 11px;border-radius:100px;border:1px solid var(--green);color:var(--green);font-size:12px;font-weight:800;letter-spacing:.06em;text-decoration:none;background:var(--white)}
.palabras a:hover{background:var(--green);color:#fff}
.palabras-bloque{margin-top:18px;display:grid;grid-template-columns:auto 1fr;gap:14px;align-items:center}
.palabras-bloque > span{font-size:11px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.avisos{margin-top:22px;padding:18px 22px;border-left:5px solid var(--red);background:var(--white)}
.avisos strong{display:block;margin-bottom:6px}
.avisos ul{margin:0;padding-left:18px;color:var(--muted);font-size:14px}
.section{padding:48px 0;scroll-margin-top:24px}
.section-head{display:flex;justify-content:space-between;align-items:end;gap:24px;margin-bottom:22px}
.section-head h2{font-size:clamp(30px,4.4vw,52px);letter-spacing:-.045em;line-height:1;margin:10px 0 0}
.section-head p{max-width:460px;margin:0;color:var(--muted);line-height:1.55}
.semana{background:var(--green);color:#fff;margin-top:18px}
.semana-head{display:flex;justify-content:space-between;align-items:baseline;gap:12px;padding:16px 20px;border-bottom:1px solid rgba(255,255,255,.16)}
.semana-head h3{margin:0;font-size:18px;letter-spacing:-.01em}
.semana-head span{color:#b9d1cc;font-size:13px;text-align:right}
.dias{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:1px;background:rgba(255,255,255,.14)}
.dia{background:var(--green);padding:14px 12px 16px;min-height:150px;min-width:0}
.dia.fuera{background:#0b302c;color:rgba(255,255,255,.4)}
.dia-fecha{display:flex;align-items:baseline;gap:6px;font-size:11px;color:#b9d1cc;text-transform:uppercase;letter-spacing:.1em}
.dia-fecha strong{font-size:22px;line-height:1;color:#ff7d70;letter-spacing:-.02em}
.dia.fuera .dia-fecha strong,.dia.libre .dia-fecha strong{color:rgba(255,255,255,.45)}
.entrada{display:block;margin-top:10px;padding:10px;background:rgba(255,255,255,.08);border-left:3px solid var(--red);text-decoration:none;font-size:13px;line-height:1.35;overflow-wrap:anywhere}
.entrada:hover,.entrada:focus-visible{background:rgba(255,255,255,.18)}
.entrada small{display:block;color:#b9d1cc;font-size:10px;font-weight:700;letter-spacing:.08em;text-transform:uppercase}
.entrada span{display:block;margin-top:5px}
.entrada b{display:block;margin-top:6px;font-size:11px;letter-spacing:.08em}
.pubs{display:grid;gap:24px}
.pub{display:grid;grid-template-columns:minmax(0,400px) minmax(0,1fr);background:var(--white);border:1px solid var(--line);scroll-margin-top:84px}
.pub-media{background:#e9e5da;border-right:1px solid var(--line);min-width:0}
.marco{position:sticky;top:72px}
.marco img{display:block;width:100%;height:auto}
.etiqueta{display:flex;justify-content:space-between;gap:12px;margin:0;padding:11px 14px;background:var(--green);color:#fff;font-size:11px;font-weight:800;letter-spacing:.1em;text-transform:uppercase}
.etiqueta span:last-child{color:#b9d1cc}
.carrusel{display:flex;align-items:flex-start;gap:8px;overflow-x:auto;scroll-snap-type:x mandatory;scrollbar-width:thin;scrollbar-color:var(--green) transparent;outline-offset:-3px}
.slide{position:relative;flex:0 0 88%;margin:0;scroll-snap-align:start}
.slide figcaption{position:absolute;right:10px;bottom:10px;background:rgba(21,21,21,.78);color:#fff;font-size:11px;font-weight:700;padding:4px 9px;border-radius:100px}
.pista{margin:0;padding:10px 14px 14px;font-size:12px;color:var(--muted)}
.reel{display:flex;flex-direction:column;align-items:center;gap:16px;background:var(--green);padding:8px 24px 24px}
.reel video{display:block;width:100%;max-width:300px;aspect-ratio:9/16;background:#000;border-radius:12px}
.pendiente{display:grid;place-items:center;aspect-ratio:4/5;margin:16px;padding:28px;border:2px dashed var(--red);color:var(--red);font-weight:700;text-align:center;background:var(--white)}
.pub-body{padding:26px 30px 28px;min-width:0}
.pub-fecha{margin:0;color:var(--red);font-size:12px;font-weight:800;letter-spacing:.12em;text-transform:uppercase}
.pub h3{margin:10px 0 14px;font-size:clamp(22px,2.4vw,28px);line-height:1.1;letter-spacing:-.03em}
.ficha{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1px;margin:0 0 22px;background:var(--line);border:1px solid var(--line)}
.ficha div{background:var(--white);padding:12px 14px;min-width:0}
.ficha dt{font-size:10px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.ficha dd{margin:4px 0 0;font-size:14px;font-weight:700;overflow-wrap:anywhere}
.clave{display:inline-block;padding:3px 9px;border-radius:100px;background:var(--green);color:#fff;font-size:12px;letter-spacing:.06em}
.campos{margin:0}
.campos dt{margin-top:18px}
.campos dt:first-child{margin-top:0}
.campos dd{margin:6px 0 0;overflow-wrap:anywhere}
.texto{margin:0;padding:16px 18px;background:var(--paper);border-left:4px solid var(--red);white-space:pre-wrap;overflow-wrap:anywhere;font:15px/1.55 Arial,Helvetica,sans-serif}
.texto-meta{display:block;margin-top:6px;font-size:12px;color:var(--muted)}
.utm{display:grid;gap:6px;margin:0;padding:0;list-style:none}
.utm li{display:grid;grid-template-columns:78px minmax(0,1fr);gap:8px;align-items:start;font-size:12px;font-weight:700}
code{font:12px/1.45 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;overflow-wrap:anywhere;word-break:break-all}
.utm code{display:block;padding:6px 8px;background:var(--paper);font-weight:400;user-select:all}
.archivos{margin:0;padding:0;list-style:none;color:var(--muted)}
.footer{padding:36px 0 64px;border-top:1px solid var(--line);color:var(--muted);font-size:14px;display:flex;justify-content:space-between;gap:24px}
.footer p{margin:0}
@media (max-width:980px){
  .hero{grid-template-columns:1fr;gap:32px}
  .resumen{grid-template-columns:repeat(2,minmax(0,1fr))}
  .dias{grid-template-columns:1fr}
  .dia{display:grid;grid-template-columns:76px minmax(0,1fr);gap:4px 12px;min-height:0;padding:12px 16px}
  .dia-fecha{flex-direction:column;gap:4px;white-space:nowrap}
  .dia .entrada{grid-column:2;margin-top:0}
  .dia .entrada + .entrada{margin-top:8px}
  .dia.libre,.dia.fuera{display:none}
  .pub{grid-template-columns:minmax(0,340px) minmax(0,1fr)}
  .ficha{grid-template-columns:repeat(2,minmax(0,1fr))}
}
@media (max-width:720px){
  .top nav a{display:none}
  .hero{padding:40px 0 28px}
  .lead{font-size:16px}
  .section-head{display:block}
  .section-head p{margin-top:14px}
  .pub{grid-template-columns:1fr}
  .pub-media{border-right:0;border-bottom:1px solid var(--line)}
  .marco{position:relative;top:auto}
  .pub-body{padding:22px 18px 24px}
  .palabras-bloque{grid-template-columns:1fr;gap:10px}
  .utm li{grid-template-columns:1fr;gap:4px}
  .footer{display:block}
  .footer p + p{margin-top:8px}
}
@media (max-width:440px){
  .resumen{grid-template-columns:1fr}
  .stats div{padding:18px}
  .stats dd{font-size:32px}
  .semana-head{display:block}
  .semana-head span{display:block;margin-top:4px;text-align:left}
}
"""


def _esc(texto: Any) -> str:
    return html.escape(str(texto), quote=True)


def _plural(cantidad: int, singular: str, plural: str) -> str:
    return f"{cantidad} {singular if cantidad == 1 else plural}"


def _red(red: str) -> str:
    return NOMBRES_RED.get(red, red)


def _formato(pub: Dict[str, Any]) -> str:
    return f"{NOMBRES_FORMATO.get(pub['formato'], pub['formato'])} · {_plural(len(pub['piezas']), 'pieza', 'piezas')}"


def _dia_largo(dia: dt.date) -> str:
    return f"{DIAS[dia.weekday()]} {dia.day} {MESES[dia.month - 1]} {dia.year}"


def _rango_corto(desde: dt.date, hasta: dt.date) -> str:
    if desde.month == hasta.month:
        return f"{desde.day} – {hasta.day} {MESES[hasta.month - 1]}"
    return f"{desde.day} {MESES[desde.month - 1]} – {hasta.day} {MESES[hasta.month - 1]}"


def _src(pieza: str, raiz: Path, salida: Path) -> str:
    """Ruta relativa desde el HTML de salida hasta la pieza de dist/, lista para un atributo."""
    relativa = os.path.relpath((raiz / pieza).resolve(), salida.resolve().parent)
    return _esc(quote(relativa.replace(os.sep, "/")))


def _tamano(pieza: str, raiz: Path) -> str:
    """Atributos width/height de un PNG (leídos del encabezado) para que la página no salte
    mientras cargan las imágenes y los enlaces del calendario caigan en su tarjeta."""
    try:
        with open(raiz / pieza, "rb") as archivo:
            cabecera = archivo.read(24)
    except OSError:
        return ""
    if cabecera[:8] != b"\x89PNG\r\n\x1a\n" or cabecera[12:16] != b"IHDR":
        return ""
    ancho, alto = int.from_bytes(cabecera[16:20], "big"), int.from_bytes(cabecera[20:24], "big")
    return f' width="{ancho}" height="{alto}"'


def _portada(pieza: str, raiz: Path) -> Optional[str]:
    """Primer cuadro de un Reel (`<nombre>-1.png` junto al .mp4) si existe."""
    candidata = pieza[:-len(".mp4")] + "-1.png" if pieza.endswith(".mp4") else ""
    return candidata if candidata and (raiz / candidata).is_file() else None


def _medios(pub: Dict[str, Any], raiz: Path, salida: Path) -> str:
    tema = pub["tema"]
    formato = pub["formato"]
    proporcion = "9:16" if formato == "reel" else "4:5"
    etiqueta = f'<p class="etiqueta"><span>{_esc(_formato(pub))}</span><span>{proporcion}</span></p>'
    piezas = pub["piezas"]

    def pendiente(pieza: str) -> str:
        return f'<div class="pendiente">Pieza pendiente: {_esc(pieza[len("PENDIENTE:"):].strip())}</div>'

    if formato == "reel":
        partes = []
        for pieza in piezas:
            if pieza.startswith("PENDIENTE:"):
                partes.append(pendiente(pieza))
                continue
            portada = _portada(pieza, raiz)
            poster = f' poster="{_src(portada, raiz, salida)}"' if portada else ""
            partes.append(f'<video src="{_src(pieza, raiz, salida)}"{poster} controls muted playsinline '
                          f'preload="metadata" aria-label="{_esc(tema if tema.lower().startswith("reel") else "Reel: " + tema)}"></video>')
        return f'<div class="marco">{etiqueta}<div class="reel">{"".join(partes)}</div></div>'

    if formato == "carrusel" or len(piezas) > 1:
        total = len(piezas)
        slides = []
        for numero, pieza in enumerate(piezas, start=1):
            if pieza.startswith("PENDIENTE:"):
                contenido = pendiente(pieza)
            else:
                contenido = (f'<img src="{_src(pieza, raiz, salida)}"{_tamano(pieza, raiz)} '
                             f'alt="{_esc(f"{tema}: diapositiva {numero} de {total}")}" loading="lazy">')
            slides.append(f'<figure class="slide">{contenido}<figcaption>{numero}/{total}</figcaption></figure>')
        return (f'<div class="marco">{etiqueta}<div class="carrusel" role="region" tabindex="0" '
                f'aria-label="{_esc(f"Carrusel de {total} piezas: {tema}")}">{"".join(slides)}</div>'
                f'<p class="pista">Desliza para ver las {total} piezas →</p></div>')

    pieza = piezas[0]
    if pieza.startswith("PENDIENTE:"):
        return f'<div class="marco">{etiqueta}{pendiente(pieza)}</div>'
    return (f'<div class="marco">{etiqueta}<img src="{_src(pieza, raiz, salida)}"{_tamano(pieza, raiz)} '
            f'alt="{_esc(tema)}" loading="lazy"></div>')


def preview(bloque: Dict[str, Any], config: Dict[str, Any], salida: Path, raiz: Path,
            avisos: Optional[List[str]] = None, origen: str = "") -> str:
    """Página HTML autocontenida para revisar y aprobar un bloque válido.

    `salida` es la ruta donde se guardará el HTML: las piezas se enlazan con rutas
    relativas desde ahí hasta `dist/`, así funciona igual en local y en el sitio."""
    nombre = bloque.get("bloque") or "bloque"
    titulo = bloque.get("titulo") or nombre
    inicio, fin = bd.fecha(bloque["inicio"]), bd.fecha(bloque["fin"])
    pubs = sorted(bloque["publicaciones"], key=lambda p: (p["fecha"], p["id"]))
    reels = sum(1 for p in pubs if p["formato"] == "reel")
    palabras: Dict[str, str] = {}  # palabra clave -> id de su primera publicación
    for pub in pubs:
        palabras.setdefault(pub["palabra_clave"], pub["id"])
    semanas = list(bd.semanas(inicio, fin))
    numero_semana = {lunes_semana: numero for numero, lunes_semana in enumerate(semanas, start=1)}
    campana = bloque.get("utm_campaign", config["utm_campaign_organico"])
    por_dia: Dict[dt.date, List[Dict[str, Any]]] = defaultdict(list)
    for pub in pubs:
        por_dia[dt.datetime.fromisoformat(pub["fecha"]).date()].append(pub)

    h: List[str] = []
    agregar = h.append
    agregar("<!doctype html>")
    agregar('<html lang="es-MX">')
    agregar("<head>")
    agregar('<meta charset="utf-8">')
    agregar('<meta name="viewport" content="width=device-width,initial-scale=1">')
    agregar('<meta name="robots" content="noindex,nofollow">')
    agregar(f'<link rel="icon" type="image/svg+xml" href="{FAVICON}">')
    agregar(f"<title>{_esc('Vista previa — ' + titulo)}</title>")
    agregar(f"<style>{PREVIEW_CSS}</style>")
    agregar("</head>")
    agregar("<body>")
    agregar('<header class="top"><div class="wrap"><span class="brand">BZA Creative</span>'
            '<nav aria-label="Secciones"><a href="#calendario">Calendario</a>'
            '<a href="#publicaciones">Publicaciones</a>'
            '<span class="badge">VISTA PREVIA INTERNA</span></nav></div></header>')
    agregar("<main>")

    agregar('<section class="hero wrap" aria-labelledby="titulo-bloque"><div>')
    agregar(f'<p class="eyebrow">{_esc(nombre)} · contenido orgánico · {_esc(_rango_corto(inicio, fin))}</p>')
    agregar(f'<h1 id="titulo-bloque">{_esc(titulo)}</h1>')
    if bloque.get("objetivo"):
        agregar(f'<p class="lead">{_esc(bloque["objetivo"])}</p>')
    agregar("</div>")
    agregar('<dl class="stats">'
            f'<div><dt>Publicaciones</dt><dd>{len(pubs) - reels}</dd></div>'
            f'<div><dt>Reels</dt><dd>{reels}</dd></div>'
            f'<div><dt>Semanas</dt><dd>{len(semanas)}</dd></div>'
            f'<div><dt>Palabras clave</dt><dd>{len(palabras)}</dd></div>'
            "</dl></section>")

    agregar('<section class="wrap" aria-label="Resumen del bloque">')
    agregar('<dl class="resumen">'
            f'<div><dt>Periodo</dt><dd>{_esc(_dia_largo(inicio))} a {_esc(_dia_largo(fin))}</dd></div>'
            f'<div><dt>Total</dt><dd>{len(pubs)} en el calendario: '
            f'{_plural(len(pubs) - reels, "publicación", "publicaciones")} y {_plural(reels, "Reel", "Reels")}</dd></div>'
            f'<div><dt>Redes y horario</dt><dd>{_esc(", ".join(_red(r) for r in config["redes"]))} · '
            f'{_esc(config["zona_horaria"])}</dd></div>'
            f'<div><dt>Campaña UTM</dt><dd><code>{_esc(campana)}</code></dd></div>'
            "</dl>")
    agregar('<div class="palabras-bloque"><span>Palabras clave</span><ul class="palabras">'
            + "".join(f'<li><a href="#{_esc(destino)}">{_esc(palabra)}</a></li>' for palabra, destino in palabras.items())
            + "</ul></div>")
    if avisos:
        agregar('<div class="avisos" role="note"><strong>Avisos de validación</strong><ul>'
                + "".join(f"<li>{_esc(a)}</li>" for a in avisos) + "</ul></div>")
    agregar("</section>")

    agregar('<section class="section wrap" id="calendario" aria-labelledby="titulo-calendario">')
    agregar('<div class="section-head"><div><p class="eyebrow">Calendario</p>'
            '<h2 id="titulo-calendario">Semana por semana</h2></div>'
            f'<p>Horario de {_esc(config["zona_horaria"])}. Cada entrada lleva a su publicación.</p></div>')
    for numero, lunes_semana in enumerate(semanas, start=1):
        domingo = lunes_semana + dt.timedelta(days=6)
        de_semana = [p for d in range(7) for p in por_dia.get(lunes_semana + dt.timedelta(days=d), [])]
        reels_semana = sum(1 for p in de_semana if p["formato"] == "reel")
        cuenta = _plural(len(de_semana) - reels_semana, "publicación", "publicaciones")
        if reels_semana:
            cuenta += " · " + _plural(reels_semana, "Reel", "Reels")
        agregar(f'<article class="semana"><div class="semana-head"><h3>Semana {numero} · '
                f'{_esc(_rango_corto(lunes_semana, domingo))}</h3><span>{_esc(cuenta)}</span></div><ol class="dias">')
        for desplazamiento in range(7):
            dia = lunes_semana + dt.timedelta(days=desplazamiento)
            del_dia = por_dia.get(dia, [])
            clase = "dia" + (" fuera" if not inicio <= dia <= fin else "" if del_dia else " libre")
            celda = [f'<li class="{clase}"><span class="dia-fecha"><strong>{dia.day}</strong>'
                     f'{_esc(DIAS_CORTOS[dia.weekday()])} · {_esc(MESES[dia.month - 1])}</span>']
            for pub in del_dia:
                hora = dt.datetime.fromisoformat(pub["fecha"]).strftime("%H:%M")
                celda.append(f'<a class="entrada" href="#{_esc(pub["id"])}"><small>{_esc(hora)} · '
                             f'{_esc(pub["formato"])}</small><span>{_esc(pub["tema"])}</span>'
                             f'<b>{_esc(pub["palabra_clave"])}</b></a>')
            celda.append("</li>")
            agregar("".join(celda))
        agregar("</ol></article>")
    agregar("</section>")

    agregar('<section class="section wrap" id="publicaciones" aria-labelledby="titulo-publicaciones">')
    agregar('<div class="section-head"><div><p class="eyebrow">Publicaciones</p>'
            '<h2 id="titulo-publicaciones">Pieza por pieza</h2></div>'
            "<p>Texto completo, historia y enlace con UTM de cada publicación, tal como se programará.</p></div>")
    agregar('<div class="pubs">')
    for pub in pubs:
        momento = dt.datetime.fromisoformat(pub["fecha"])
        texto = pub["texto"]
        hashtags = len(re.findall(r"#\w+", texto))
        agregar(f'<article class="pub" id="{_esc(pub["id"])}">')
        agregar(f'<div class="pub-media">{_medios(pub, raiz, salida)}</div>')
        agregar('<div class="pub-body">')
        agregar(f'<p class="pub-fecha">{_esc(pub["id"])} · semana {numero_semana[bd.lunes(momento.date())]}</p>')
        agregar(f'<h3>{_esc(pub["tema"])}</h3>')
        agregar('<dl class="ficha">'
                f'<div><dt>Fecha</dt><dd>{_esc(_fecha_larga(momento))}</dd></div>'
                f'<div><dt>Formato</dt><dd>{_esc(_formato(pub))}</dd></div>'
                f'<div><dt>Palabra clave</dt><dd><span class="clave">{_esc(pub["palabra_clave"])}</span></dd></div>'
                f'<div><dt>Redes</dt><dd>{_esc(", ".join(_red(r) for r in pub["redes"]))}</dd></div>'
                "</dl>")
        agregar('<dl class="campos">')
        if pub.get("objetivo"):
            agregar(f'<dt>Objetivo</dt><dd>{_esc(pub["objetivo"])}</dd>')
        agregar(f'<dt>Texto</dt><dd><p class="texto">{_esc(texto)}</p>'
                f'<span class="texto-meta">{len(texto)} caracteres · {hashtags} hashtags</span></dd>')
        if pub.get("historia"):
            agregar(f'<dt>Historia (17:00–18:00)</dt><dd>{_esc(pub["historia"])}</dd>')
        agregar('<dt>Enlace con UTM</dt><dd><ul class="utm">'
                + "".join(f"<li>{_esc(_red(red))}<code>{_esc(enlace(bloque, pub, red, config))}</code></li>"
                          for red in pub["redes"])
                + "</ul></dd>")
        agregar('<dt>Archivos</dt><dd><ul class="archivos">'
                + "".join(f"<li><code>{_esc(p)}</code></li>" for p in pub["piezas"]) + "</ul></dd>")
        agregar("</dl></div></article>")
    agregar("</div></section>")
    agregar("</main>")
    agregar('<footer class="footer wrap">'
            f'<p><strong>BZA Creative</strong> · Vista previa interna de {_esc(titulo)}. No se indexa.</p>'
            f'<p>Generada con <code>calendario.py preview</code>{" desde <code>" + _esc(origen) + "</code>" if origen else ""}.</p>'
            "</footer>")
    agregar("</body>")
    agregar("</html>")
    return "\n".join(h) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("accion", choices=["validar", "markdown", "metricool", "preview"])
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

    if args.accion == "preview":
        destino = args.salida or raiz / "dist" / "campana-preview" / args.bloque.stem / "index.html"
        try:
            origen = Path(os.path.relpath(args.bloque.resolve(), Path(raiz).resolve())).as_posix()
        except ValueError:
            origen = args.bloque.name
        if origen.startswith("../"):
            origen = args.bloque.name
        pagina = preview(bloque, config, destino, raiz, avisos, origen)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(pagina, encoding="utf-8")
        print(f"Escrito {destino} ({len(bloque['publicaciones'])} publicaciones, {len(avisos)} avisos)")
        dist = (Path(raiz) / "dist").resolve()
        carpeta = destino.resolve().parent
        if not carpeta.is_relative_to(dist):
            print("AVISO  la salida está fuera de dist/: las rutas a las piezas solo funcionan en esta máquina")
        elif destino.name == "index.html":
            print(f"URL después del despliegue: {config['sitio']}{carpeta.relative_to(dist).as_posix()}/")
        return 0

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

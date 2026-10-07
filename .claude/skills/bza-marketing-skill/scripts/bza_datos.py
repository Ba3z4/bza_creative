"""Utilidades compartidas del agente de marketing de BZA Creative.

Lee la configuración, los tres registros CSV de `marketing/datos/` y resuelve
las semanas de reporte (lunes a domingo, hora de Ciudad de México).
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import unicodedata
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

SKILL_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = SKILL_DIR / "assets" / "config.json"

# México no aplica horario de verano desde octubre de 2022: el desfase es fijo.
ZONA_MX = dt.timezone(dt.timedelta(hours=-6), "America/Mexico_City")

CANALES_PAGADOS = ("google_ads", "meta_ads")
ETAPAS = ("nuevo", "calificado", "diagnostico", "propuesta", "negociacion", "ganado")

COLUMNAS_METRICAS = [
    "semana_inicio", "canal", "tipo", "inversion_mxn", "impresiones", "alcance",
    "clics", "interacciones", "guardados", "compartidos", "visitas_perfil",
    "seguidores_nuevos", "mensajes", "clics_whatsapp", "contactos_enviados", "fuente",
]
COLUMNAS_CONVERSACIONES = [
    "id", "fecha", "canal", "palabra_clave", "servicio", "sector", "calificada",
    "etapa", "valor_estimado_mxn", "valor_cerrado_mxn", "notas",
]
COLUMNAS_PUBLICACIONES = [
    "fecha", "red", "tema", "palabra_clave", "formato", "alcance", "interacciones",
    "guardados", "compartidos", "mensajes_palabra_clave", "clics_enlace",
]

ARCHIVOS = {
    "metricas": ("metricas-semanales.csv", COLUMNAS_METRICAS),
    "conversaciones": ("conversaciones.csv", COLUMNAS_CONVERSACIONES),
    "publicaciones": ("publicaciones.csv", COLUMNAS_PUBLICACIONES),
}


def cargar_config(ruta: Optional[Path] = None) -> Dict[str, Any]:
    """Carga `assets/config.json` (o la ruta indicada)."""
    with open(ruta or CONFIG_PATH, encoding="utf-8") as archivo:
        return json.load(archivo)


def raiz_repo(inicio: Optional[Path] = None) -> Path:
    """Devuelve el directorio que contiene `marketing/`, buscando hacia arriba."""
    for base in (inicio or Path.cwd(), SKILL_DIR):
        for candidato in (base, *base.resolve().parents):
            if (candidato / "marketing").is_dir():
                return candidato
    return Path.cwd()


def datos_por_defecto() -> Path:
    return raiz_repo() / "marketing" / "datos"


def leer_csv(ruta: Path, columnas: List[str]) -> List[Dict[str, str]]:
    """Lee un CSV con encabezado. Si no existe devuelve lista vacía.

    Falla con un mensaje claro cuando faltan columnas obligatorias.
    """
    if not ruta.exists():
        return []
    with open(ruta, encoding="utf-8-sig", newline="") as archivo:
        lector = csv.DictReader(archivo)
        encabezado = [c.strip() for c in (lector.fieldnames or [])]
        faltan = [c for c in columnas if c not in encabezado]
        if faltan:
            raise ValueError(f"{ruta.name}: faltan columnas {', '.join(faltan)}")
        filas = []
        for numero_fila, fila in enumerate(lector, start=2):
            limpia = {(k or "").strip(): (v or "").strip() for k, v in fila.items()}
            if not any(limpia.values()):
                continue
            limpia["_fila"] = str(numero_fila)
            filas.append(limpia)
        return filas


def cargar_datos(directorio: Path) -> Dict[str, List[Dict[str, str]]]:
    return {clave: leer_csv(directorio / nombre, cols) for clave, (nombre, cols) in ARCHIVOS.items()}


def numero(valor: Any) -> float:
    """Convierte '1,250', '$858' o '' a número. Vacío equivale a 0."""
    if valor is None:
        return 0.0
    texto = str(valor).replace("$", "").replace(",", "").replace("MXN", "").strip()
    if not texto:
        return 0.0
    try:
        return float(texto)
    except ValueError as error:
        raise ValueError(f"valor numérico inválido: {valor!r}") from error


def normalizar(texto: str) -> str:
    """Minúsculas sin acentos: 'Sí' -> 'si', 'Diagnóstico' -> 'diagnostico'."""
    base = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in base if not unicodedata.combining(c)).lower().strip()


def fecha(valor: str) -> dt.date:
    """Acepta 'AAAA-MM-DD' o una fecha-hora ISO; devuelve la fecha."""
    texto = (valor or "").strip()
    if not texto:
        raise ValueError("fecha vacía")
    return dt.date.fromisoformat(texto[:10])


def lunes(dia: dt.date) -> dt.date:
    return dia - dt.timedelta(days=dia.weekday())


def hoy_mx() -> dt.date:
    return dt.datetime.now(ZONA_MX).date()


def semana_reporte(referencia: Optional[dt.date] = None) -> dt.date:
    """Lunes de la última semana completa antes de `referencia`."""
    return lunes(referencia or hoy_mx()) - dt.timedelta(days=7)


def semanas(desde: dt.date, hasta: dt.date) -> Iterable[dt.date]:
    actual = lunes(desde)
    while actual <= hasta:
        yield actual
        actual += dt.timedelta(days=7)


def es_si(valor: str) -> bool:
    return normalizar(valor) in {"si", "s", "yes", "true", "1"}


def indice_etapa(etapa: str) -> int:
    """Posición de la etapa en el embudo; -1 para 'perdido' o desconocida."""
    try:
        return ETAPAS.index(normalizar(etapa))
    except ValueError:
        return -1


def mxn(valor: Optional[float]) -> str:
    if valor is None:
        return "—"
    return f"${valor:,.0f} MXN"


def pct(valor: Optional[float]) -> str:
    return "—" if valor is None else f"{valor * 100:.1f}%"

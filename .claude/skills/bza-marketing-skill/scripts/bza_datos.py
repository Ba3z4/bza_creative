"""Utilidades compartidas del agente de marketing de BZA Creative.

Lee la configuración, los tres registros CSV de `marketing/datos/`, los valida
fila por fila (`validar_datos`) y resuelve las semanas de reporte (lunes a domingo,
hora de Ciudad de México).
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

SKILL_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = SKILL_DIR / "assets" / "config.json"

# México no aplica horario de verano desde octubre de 2022: el desfase es fijo.
ZONA_MX = dt.timezone(dt.timedelta(hours=-6), "America/Mexico_City")

CANALES_PAGADOS = ("google_ads", "meta_ads")
# Valores documentados de `canal` (SKILL.md → Registrar y marketing/README.md).
CANALES = ("facebook", "instagram", "google_ads", "meta_ads", "google_organico", "sitio",
           "prospeccion", "referido", "directo")
ETAPAS = ("nuevo", "calificado", "diagnostico", "propuesta", "negociacion", "ganado")
ETAPAS_VALIDAS = ETAPAS + ("perdido",)
CALIFICADA = ("si", "no", "pendiente")
# Fecha en que ocurrió cada etapa (opcional). Vacía: se usa `fecha` si la etapa ya se alcanzó.
FECHAS_ETAPA = {"diagnostico": "fecha_diagnostico", "propuesta": "fecha_propuesta", "ganado": "fecha_cierre"}

COLUMNAS_METRICAS = [
    "semana_inicio", "canal", "tipo", "inversion_mxn", "impresiones", "alcance",
    "clics", "interacciones", "guardados", "compartidos", "visitas_perfil",
    "seguidores_nuevos", "mensajes", "clics_whatsapp", "contactos_enviados", "fuente",
]
COLUMNAS_CONVERSACIONES = [
    "id", "fecha", "canal", "palabra_clave", "servicio", "sector", "calificada",
    "etapa", "valor_estimado_mxn", "valor_cerrado_mxn", "notas",
]
# Opcionales: los archivos anteriores no las traen y se leen igual (valor vacío).
COLUMNAS_OPCIONALES_CONVERSACIONES = list(FECHAS_ETAPA.values())
COLUMNAS_PUBLICACIONES = [
    "fecha", "red", "tema", "palabra_clave", "formato", "alcance", "interacciones",
    "guardados", "compartidos", "mensajes_palabra_clave", "clics_enlace",
]

ARCHIVOS = {
    "metricas": ("metricas-semanales.csv", COLUMNAS_METRICAS, []),
    "conversaciones": ("conversaciones.csv", COLUMNAS_CONVERSACIONES, COLUMNAS_OPCIONALES_CONVERSACIONES),
    "publicaciones": ("publicaciones.csv", COLUMNAS_PUBLICACIONES, []),
}

# Columnas numéricas por archivo; solo `seguidores_nuevos` (neto) puede ser negativa.
NUMERICAS = {
    "metricas": ["inversion_mxn", "impresiones", "alcance", "clics", "interacciones", "guardados",
                 "compartidos", "visitas_perfil", "seguidores_nuevos", "mensajes", "clics_whatsapp",
                 "contactos_enviados"],
    "conversaciones": ["valor_estimado_mxn", "valor_cerrado_mxn"],
    "publicaciones": ["alcance", "interacciones", "guardados", "compartidos",
                      "mensajes_palabra_clave", "clics_enlace"],
}
PUEDEN_SER_NEGATIVAS = {"seguidores_nuevos"}
MAX_ERRORES = 25


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


def preparar_consola() -> None:
    """En Windows, una consola o una redirección en cp1252 no debe fallar por '→' o '—'."""
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass


def dentro_de(ruta: Path, base: Path) -> bool:
    """`ruta.is_relative_to(base)` compatible con Python 3.8."""
    try:
        ruta.relative_to(base)
    except ValueError:
        return False
    return True


def datos_por_defecto() -> Path:
    return raiz_repo() / "marketing" / "datos"


def leer_csv(ruta: Path, columnas: List[str], opcionales: Iterable[str] = ()) -> List[Dict[str, str]]:
    """Lee un CSV con encabezado. Si no existe devuelve lista vacía.

    Falla con un mensaje claro cuando faltan columnas obligatorias o una fila trae
    más valores que el encabezado. Las columnas `opcionales` que no estén en el
    archivo quedan como texto vacío. Cada fila guarda en `_fila` la línea del archivo
    donde empieza (la misma que muestra una hoja de cálculo; el encabezado es la 1).
    """
    if not ruta.exists():
        return []
    try:
        return _leer_csv(ruta, columnas, opcionales)
    except UnicodeDecodeError:
        raise ValueError(f"{ruta.name}: no está en UTF-8. En Excel, guardar como "
                         "«CSV UTF-8 (delimitado por comas)».") from None


def _leer_csv(ruta: Path, columnas: List[str], opcionales: Iterable[str]) -> List[Dict[str, str]]:
    with open(ruta, encoding="utf-8-sig", newline="") as archivo:
        lector = csv.DictReader(archivo)
        encabezado = [c.strip() for c in (lector.fieldnames or [])]
        faltan = [c for c in columnas if c not in encabezado]
        if faltan:
            raise ValueError(f"{ruta.name}: faltan columnas {', '.join(faltan)}")
        filas = []
        for fila in lector:
            # line_num es la última línea leída; se restan los saltos de línea dentro de celdas.
            numero_fila = lector.line_num - sum(str(v).count("\n") for v in fila.values() if v)
            if None in fila:
                raise ValueError(
                    f"{ruta.name} fila {numero_fila}: tiene {len(fila[None])} valor(es) más que el encabezado. "
                    "Si un número lleva coma de miles, escríbelo entre comillas (\"1,400\") o sin coma (1400).")
            limpia = {(k or "").strip(): (v or "").strip() for k, v in fila.items()}
            if not any(limpia.values()):
                continue
            for columna in opcionales:
                limpia.setdefault(columna, "")
            limpia["_fila"] = str(numero_fila)
            filas.append(limpia)
        return filas


def cargar_datos(directorio: Path) -> Dict[str, List[Dict[str, str]]]:
    return {clave: leer_csv(directorio / nombre, cols, opcionales)
            for clave, (nombre, cols, opcionales) in ARCHIVOS.items()}


# Solo formato de México/EE. UU.: coma para miles (grupos de 3) y punto con 1 o 2 decimales.
# '1.400' (miles con punto), '858,50' (decimal con coma), 'nan' o 'inf' se rechazan.
_NUMERO = re.compile(r"(-)?\$?\s*(\d{1,3}(?:,\d{3})+|\d+)(\.\d{1,2})?(?:\s*MXN)?", re.IGNORECASE)


def numero(valor: Any) -> float:
    """Convierte '1400', '1400.5', '1,400', '1,400.50', '$858' o '858 MXN' a número.

    Vacío equivale a 0. Cualquier otro formato lanza ValueError (quien llama agrega
    archivo y fila)."""
    if valor is None:
        return 0.0
    texto = str(valor).strip()
    if not texto:
        return 0.0
    coincide = _NUMERO.fullmatch(texto)
    if not coincide:
        raise ValueError(f"{texto!r} no es un número válido (usar 1400, 1,400 o 1,400.50: "
                         "coma para miles y punto para decimales)")
    signo, entero, decimales = coincide.groups()
    resultado = float(entero.replace(",", "") + (decimales or ""))
    return -resultado if signo else resultado


def normalizar(texto: str) -> str:
    """Minúsculas sin acentos: 'Sí' -> 'si', 'Diagnóstico' -> 'diagnostico'."""
    base = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in base if not unicodedata.combining(c)).lower().strip()


def canal(valor: str) -> str:
    """Forma canónica de un canal: 'Google Ads', 'google-ads' o 'GOOGLE_ADS' -> 'google_ads'."""
    return re.sub(r"[\s\-_]+", "_", normalizar(valor)).strip("_")


def fecha(valor: str) -> dt.date:
    """Acepta 'AAAA-MM-DD' o una fecha-hora ISO ('AAAA-MM-DDTHH:MM'); devuelve la fecha."""
    texto = (valor or "").strip()
    if not texto:
        raise ValueError("fecha vacía")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:[T ].*)?", texto):
        raise ValueError(f"{texto!r} no es una fecha AAAA-MM-DD")
    try:
        return dt.date.fromisoformat(texto[:10])
    except ValueError as error:
        raise ValueError(f"{texto!r} no es una fecha válida ({error})") from None


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
    return normalizar(valor) == "si"


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


class DatosInvalidos(ValueError):
    """Errores de validación; cada línea empieza con '<archivo> fila <n>: '."""

    def __init__(self, errores: List[str]):
        self.errores = errores
        extra = len(errores) - MAX_ERRORES
        lineas = errores[:MAX_ERRORES] + ([f"… y {extra} errores más"] if extra > 0 else [])
        super().__init__("\n".join(lineas))


def validar_datos(datos: Dict[str, List[Dict[str, str]]]) -> None:
    """Revisa cada fila de los tres CSV y deja `canal`, `etapa` y `calificada` en su forma
    canónica. Lanza `DatosInvalidos` con '<archivo> fila <n>: …' por cada problema."""
    errores: List[str] = []
    for clave, (nombre, _, _) in ARCHIVOS.items():
        vistos: Dict[Any, str] = {}
        for fila in datos.get(clave, []):
            prefijo = f"{nombre} fila {fila.get('_fila', '?')}"
            problemas = _validar_fila(clave, fila, vistos)
            errores.extend(f"{prefijo}: {problema}" for problema in problemas)
    if errores:
        raise DatosInvalidos(errores)


def _validar_fila(clave: str, fila: Dict[str, str], vistos: Dict[Any, str]) -> List[str]:
    problemas: List[str] = []

    def revisar_fecha(columna: str, obligatoria: bool = True) -> Optional[dt.date]:
        valor = fila.get(columna, "")
        if not valor:
            if obligatoria:
                problemas.append(f"{columna} vacía (usar AAAA-MM-DD)")
            return None
        try:
            return fecha(valor)
        except ValueError:
            problemas.append(f"{columna} {valor!r} no es una fecha válida (usar AAAA-MM-DD)")
            return None

    for columna in NUMERICAS[clave]:
        try:
            if numero(fila.get(columna)) < 0 and columna not in PUEDEN_SER_NEGATIVAS:
                problemas.append(f"{columna} {fila[columna]!r} no puede ser negativo")
        except ValueError as error:
            problemas.append(f"{columna} {error}")

    if clave in ("metricas", "conversaciones"):
        original = fila.get("canal", "")
        canonico = canal(original)
        if canonico in CANALES:
            fila["canal"] = canonico
        elif original or clave == "metricas":
            problemas.append(f"canal {original!r} no es válido (usar: {', '.join(CANALES)})")

    if clave == "metricas":
        semana = revisar_fecha("semana_inicio")
        if semana and fila["canal"] in CANALES:
            llave = (lunes(semana), fila["canal"])
            if llave in vistos:
                problemas.append(f"semana {llave[0]} y canal {llave[1]} repetidos (ya están en la fila "
                                 f"{vistos[llave]}): debe haber una sola fila por semana y canal")
            else:
                vistos[llave] = fila.get("_fila", "?")
    elif clave == "publicaciones":
        revisar_fecha("fecha")
    else:
        inicio = revisar_fecha("fecha")
        etapa = normalizar(fila.get("etapa", "")) or "nuevo"
        if etapa in ETAPAS_VALIDAS:
            fila["etapa"] = etapa
        else:
            problemas.append(f"etapa {fila['etapa']!r} no es válida (usar: {', '.join(ETAPAS_VALIDAS)})")
        calificada = normalizar(fila.get("calificada", ""))
        if calificada in CALIFICADA:
            fila["calificada"] = calificada
        else:
            problemas.append(f"calificada {fila.get('calificada', '')!r} no es válida (usar si, no o pendiente)")
        for etapa_fecha, columna in FECHAS_ETAPA.items():
            dia = revisar_fecha(columna, obligatoria=False)
            if dia is None:
                continue
            if inicio and dia < inicio:
                problemas.append(f"{columna} {dia} es anterior a la fecha de la conversación ({inicio})")
            if etapa in ETAPAS_VALIDAS and not alcanzo(etapa, etapa_fecha, fecha_explicita=True):
                problemas.append(f"{columna} tiene fecha pero la etapa es {etapa!r}: actualizar la etapa o "
                                 "borrar la fecha (solo se anota cuando la etapa ya ocurrió)")
        identificador = fila.get("id", "")
        if identificador:
            if identificador in vistos:
                problemas.append(f"id {identificador} repetido (ya está en la fila {vistos[identificador]}): "
                                 "actualizar esa fila en lugar de agregar otra")
            else:
                vistos[identificador] = fila.get("_fila", "?")
    return problemas


def alcanzo(etapa_actual: str, etapa: str, fecha_explicita: bool = False) -> bool:
    """¿Una conversación en `etapa_actual` ya pasó por `etapa`?

    'perdido' no dice hasta dónde llegó: solo cuenta una etapa intermedia si su fecha
    está anotada. 'ganado' solo lo alcanza una conversación ganada; `fecha_cierre`
    también puede anotarse en una perdida."""
    if etapa == "ganado":
        return etapa_actual == "ganado" or (fecha_explicita and etapa_actual == "perdido")
    if etapa_actual == "perdido":
        return fecha_explicita
    return indice_etapa(etapa_actual) >= ETAPAS.index(etapa)


def fecha_etapa(conversacion: Dict[str, str], etapa: str) -> Optional[dt.date]:
    """Día en que la conversación llegó a `etapa` ('diagnostico', 'propuesta' o 'ganado').

    Usa la columna de fecha de esa etapa; si está vacía y la etapa ya se alcanzó, la
    `fecha` de la conversación (así cuentan las filas anteriores a esas columnas).
    Devuelve None si la conversación no llegó a esa etapa."""
    actual = normalizar(conversacion.get("etapa", "")) or "nuevo"
    if etapa == "ganado" and actual != "ganado":
        return None
    explicita = conversacion.get(FECHAS_ETAPA[etapa], "")
    if explicita and alcanzo(actual, etapa, fecha_explicita=True):
        return fecha(explicita)
    if alcanzo(actual, etapa):
        return fecha(conversacion["fecha"])
    return None

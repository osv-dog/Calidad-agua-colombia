"""
Módulo de carga y recuperación de datos desde PostgreSQL / Neon.
"""

from typing import Dict, Optional
import pandas as pd
import streamlit as st
from sqlalchemy.engine import URL
from streamlit.errors import StreamlitSecretNotFoundError

MAPEO_COLUMNAS_POSTGRES: Dict[str, str] = {
    # Nombres reales de la tabla en PostgreSQL / Neon (tabla irca)
    "departamento_codigo": "DepartamentoCodigo",
    "departamento": "Departamento",
    "municipio_codigo": "MunicipioCodigo",
    "municipio": "Municipio",
    "anio": "Año",
    "es_agregado_departamental": "es_agregado_departamental",
    "irca": "IRCA",
    "nivel_riesgo": "Nivel de riesgo",
    "irca_urbano": "IRCAurbano",
    "nivel_riesgo_urbano": "Nivel de riesgo urbano",
    "irca_rural": "IRCArural",
    "nivel_riesgo_rural": "Nivel de riesgo rural",
    # Variantes históricas o defensivas
    "departamentocodigo": "DepartamentoCodigo",
    "municipiocodigo": "MunicipioCodigo",
    "a_o": "Año",
    "ano": "Año",
    "nivel_de_riesgo": "Nivel de riesgo",
    "ircaurbano": "IRCAurbano",
    "nivel_de_riesgo_urbano": "Nivel de riesgo urbano",
    "ircarural": "IRCArural",
    "nivel_de_riesgo_rural": "Nivel de riesgo rural",
}


def obtener_conexion_postgres() -> Optional[URL]:
    """
    Construye la conexión PostgreSQL con los valores editables de .streamlit/secrets.toml.
    """
    try:
        configuracion = st.secrets["postgres"]
    except (KeyError, StreamlitSecretNotFoundError):
        return None

    campos_requeridos = ("DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME")
    campos_faltantes = [campo for campo in campos_requeridos if not configuracion.get(campo)]
    if campos_faltantes:
        raise ValueError(
            "Faltan estos valores en la sección [postgres] de .streamlit/secrets.toml: "
            + ", ".join(campos_faltantes)
        )

    return URL.create(
        "postgresql+psycopg2",
        username=configuracion["DB_USER"],
        password=configuracion["DB_PASSWORD"],
        host=configuracion["DB_HOST"],
        port=int(configuracion["DB_PORT"]),
        database=configuracion["DB_NAME"],
        query={"sslmode": configuracion.get("DB_SSLMODE", "require")},
    )


@st.cache_data(show_spinner=False)
def cargar_datos_desde_postgres(conn_str: URL, table_name: str = "irca") -> pd.DataFrame:
    """Carga los datos crudos desde PostgreSQL / Neon en formato texto puro y renombra las columnas."""
    from sqlalchemy import create_engine
    engine = create_engine(conn_str)
    query = f"SELECT * FROM {table_name}"
    df_raw = pd.read_sql_query(query, con=engine, dtype=str)
    # Mapeo que renombra columnas en minúsculas a los nombres oficiales usados por la aplicación
    map_norm = {col: MAPEO_COLUMNAS_POSTGRES.get(col.lower().strip(), col) for col in df_raw.columns}
    df_raw = df_raw.rename(columns=map_norm)
    return df_raw

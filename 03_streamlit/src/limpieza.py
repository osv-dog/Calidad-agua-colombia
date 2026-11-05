"""
Módulo de limpieza, estandarización y transformación de datos IRCA.
Cumple con la Resolución 2115 de 2007 y estándares metodológicos de calidad de datos.
"""

from typing import List, Optional, Tuple
import numpy as np
import pandas as pd
from src.carga import MAPEO_COLUMNAS_POSTGRES

COLUMNAS_NUMERICAS: List[str] = ["IRCA", "IRCAurbano", "IRCArural"]


def clasificar_riesgo_resolucion_2115(valor: Optional[float]) -> Optional[str]:
    """
    Recalcula y clasifica el nivel de riesgo del agua según la Resolución 2115 de 2007 (Art. 15):
      - 0.0  a  5.0 %: Sin riesgo
      - 5.1  a 14.0 %: Riesgo bajo
      - 14.1 a 35.0 %: Riesgo medio
      - 35.1 a 80.0 %: Riesgo alto
      - 80.1 a 100.0%: Inviable sanitariamente
    Retorna None si el valor es nulo (ND).
    """
    if pd.isna(valor):
        return None
    val = float(valor)
    if val <= 5.0:
        return "Sin riesgo"
    elif val <= 14.0:
        return "Riesgo bajo"
    elif val <= 35.0:
        return "Riesgo medio"
    elif val <= 80.0:
        return "Riesgo alto"
    else:
        return "Inviable sanitariamente"


def calcular_limites_iqr(serie: pd.Series) -> Tuple[float, float, float, float, float]:
    """
    Calcula los cuartiles y límites de detección de atípicos según la regla de Tukey (1.5 × IQR).
    Retorna: (Q1, Q3, IQR, limite_inferior, limite_superior)
    """
    limpia = serie.dropna()
    if limpia.empty:
        return np.nan, np.nan, np.nan, np.nan, np.nan
    q1 = float(limpia.quantile(0.25))
    q3 = float(limpia.quantile(0.75))
    iqr = q3 - q1
    lim_inf = q1 - 1.5 * iqr
    lim_sup = q3 + 1.5 * iqr
    return q1, q3, iqr, lim_inf, lim_sup


def normalizar_booleano(serie: pd.Series) -> pd.Series:
    """Normaliza una serie a booleano nativo (soporta bool, str 'True'/'False', 1/0, etc.)."""
    if pd.api.types.is_bool_dtype(serie):
        return serie.fillna(False).astype(bool)
    if pd.api.types.is_numeric_dtype(serie):
        return serie.fillna(0).astype(bool)
    s_str = serie.astype(str).str.strip().str.lower()
    return s_str.isin(["true", "t", "1", "yes", "si", "sí"])


def procesar_datos_irca(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica las transformaciones analíticas sin eliminar ninguna fila del conjunto original:
      1. Normalización de nombres de columnas y mapeo de minúsculas.
      2. Conversión de 'ND' y NULL a valor nulo (np.nan), sin imputación.
      3. Tipado correcto de Año (eliminando separador de miles si existe).
      4. Tipado de variables continuas reemplazando comas decimales por puntos.
      5. Normalización de es_agregado_departamental a booleano y validación contra Municipio == '#TODOS'.
      6. Recálculo del nivel de riesgo según Resolución 2115 de 2007.
      7. Marcado de valores atípicos mediante regla 1.5 × IQR de Tukey sin eliminarlos.
    """
    df = df_raw.copy()

    # Estandarización de nombres de columnas eliminando espacios accidentales
    df.columns = [c.strip() for c in df.columns]
    map_norm = {col: MAPEO_COLUMNAS_POSTGRES.get(col.lower().strip(), col) for col in df.columns}
    df = df.rename(columns=map_norm)

    # Convertir "ND", "NULL" y variantes a valor nulo (sin imputar)
    df = df.replace(
        to_replace=["ND", "nd", "Nd", "N/D", "", "NULL", "null", "None", "nan", "<NA>"],
        value=np.nan,
    )

    # Conversión de 'Año' (tratar miles con coma como '2,024' -> 2024)
    if "Año" in df.columns:
        df["Año_Limpio"] = (
            df["Año"]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.strip()
        )
        df["Año_Num"] = pd.to_numeric(df["Año_Limpio"], errors="coerce").astype("Int64")
    elif "a_o" in df.columns:
        df["Año_Limpio"] = (
            df["a_o"]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.strip()
        )
        df["Año_Num"] = pd.to_numeric(df["Año_Limpio"], errors="coerce").astype("Int64")
    else:
        df["Año_Num"] = np.nan

    # Conversión numérica de variables cuantitativas continuas de calidad de agua
    for col in COLUMNAS_NUMERICAS:
        if col in df.columns:
            # Reemplazar comas decimales por puntos antes de convertir a numérico
            serie_str = df[col].astype(str).str.strip()
            serie_str = serie_str.mask(df[col].isna(), np.nan)
            serie_str = serie_str.str.replace(",", ".", regex=False)
            df[col + "_Num"] = pd.to_numeric(serie_str, errors="coerce")
        else:
            df[col + "_Num"] = np.nan

    # Normalizar es_agregado_departamental a booleano y sincronizar con Es_Departamental (#TODOS)
    if "Municipio" in df.columns:
        es_todos = df["Municipio"].astype(str).str.strip().str.upper() == "#TODOS"
    else:
        es_todos = pd.Series(False, index=df.index)

    if "es_agregado_departamental" in df.columns:
        df["es_agregado_departamental"] = normalizar_booleano(df["es_agregado_departamental"])
        df["Es_Departamental"] = df["es_agregado_departamental"]
    else:
        df["Es_Departamental"] = es_todos
        df["es_agregado_departamental"] = es_todos

    # Recalcular nivel de riesgo según Resolución 2115 de 2007
    df["NivelRiesgo_Recalculado"] = df["IRCA_Num"].apply(
        clasificar_riesgo_resolucion_2115
    )
    df["NivelRiesgoUrbano_Recalculado"] = df["IRCAurbano_Num"].apply(
        clasificar_riesgo_resolucion_2115
    )
    df["NivelRiesgoRural_Recalculado"] = df["IRCArural_Num"].apply(
        clasificar_riesgo_resolucion_2115
    )

    # Marcar atípicos globales (regla 1.5 × IQR de Tukey) sin eliminar filas
    for col in COLUMNAS_NUMERICAS:
        _, _, _, lim_inf, lim_sup = calcular_limites_iqr(df[col + "_Num"])
        df["Atipico_" + col] = (
            (df[col + "_Num"] < lim_inf) | (df[col + "_Num"] > lim_sup)
        ).fillna(False)

    return df

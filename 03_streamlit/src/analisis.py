"""
Módulo de cálculos analíticos, estadísticos y epidemiológicos sobre calidad del agua.
"""

from typing import Any, Dict
import numpy as np
import pandas as pd
from scipy import stats
from src.limpieza import calcular_limites_iqr, clasificar_riesgo_resolucion_2115


def obtener_descripcion_columna(
    col: str,
    min_anio: int = 0,
    max_anio: int = 0,
    anios_validos: bool = False,
) -> str:
    """Retorna la descripción funcional o rol de la columna en el conjunto de datos."""
    c = col.lower().strip()
    if "departamentocodigo" in c or "departamento_codigo" in c:
        return "Identificador DANE Depto."
    if c == "departamento":
        return "Nombre de Departamento"
    if "municipiocodigo" in c or "municipio_codigo" in c:
        return "Identificador DANE Mun."
    if c == "municipio":
        return "Nombre de Municipio / #TODOS"
    if "año" in c or "anio" in c or c == "a_o":
        return f"Año del reporte ({min_anio}-{max_anio})" if anios_validos else "Año del reporte"
    if "es_agregado_departamental" in c or "es_departamental" in c:
        return "Indicador de consolidado departamental (#TODOS)"
    if c == "irca":
        return "Índice ponderado global (0-100)"
    if c in ("nivel de riesgo", "nivel_riesgo"):
        return "Nivel de riesgo oficial del INS"
    if c in ("nivel de riesgo urbano", "nivel_riesgo_urbano"):
        return "Nivel de riesgo reportado zona urbana"
    if c in ("nivel de riesgo rural", "nivel_riesgo_rural"):
        return "Nivel de riesgo reportado zona rural"
    if c in ("ircaurbano", "irca_urbano"):
        return "IRCA sector urbano (0-100)"
    if "urbano" in c:
        return "Riesgo reportado zona urbana"
    if c in ("ircarural", "irca_rural"):
        return "IRCA sector rural (0-100)"
    if "rural" in c:
        return "Riesgo reportado zona rural"
    return "Variable complementaria"


def obtener_resumen_tipos(
    df_crudo: pd.DataFrame,
    df_completo: pd.DataFrame,
    min_anio: int = 0,
    max_anio: int = 0,
    anios_validos: bool = False,
) -> pd.DataFrame:
    """Genera la tabla comparativa de tipado y descripción funcional por columna."""
    resumen_tipos = []
    for col in df_crudo.columns:
        tipo_crudo = str(df_crudo[col].dtype)
        tipo_proc = (
            str(df_completo[col + "_Num"].dtype)
            if col + "_Num" in df_completo
            else str(df_completo[col].dtype)
        )
        conteo_no_nulos = int(df_completo[col].notna().sum())
        resumen_tipos.append({
            "Columna": col,
            "Tipo Original (Lectura)": tipo_crudo,
            "Tipo Analítico": tipo_proc,
            "No Nulos": conteo_no_nulos,
            "Descripción / Rol": obtener_descripcion_columna(col, min_anio, max_anio, anios_validos),
        })
    return pd.DataFrame(resumen_tipos)


def obtener_resumen_faltantes(df_crudo: pd.DataFrame, total_filas: int) -> pd.DataFrame:
    """Cuantifica los valores faltantes ('ND' y NULL) y calcula los porcentajes de completitud por columna."""
    faltantes_lista = []
    for col in df_crudo.columns:
        s_raw = df_crudo[col]
        cant_nd = int(_mascara_faltantes_fuente(s_raw).sum())
        pct_nd = (cant_nd / total_filas) * 100 if total_filas > 0 else 0.0
        faltantes_lista.append({
            "Variable": col,
            "Conteo Faltantes (ND/NULL)": cant_nd,
            "Porcentaje (%)": round(pct_nd, 2),
            "Completitud (%)": round(100.0 - pct_nd, 2),
        })
    return pd.DataFrame(faltantes_lista)


def _mascara_faltantes_fuente(serie: pd.Series) -> pd.Series:
    """Identifica nulos SQL y marcadores textuales de dato no disponible."""
    valores = serie.astype("string").str.strip().str.lower()
    return serie.isna() | valores.isin(["nd", "n/d", "", "null", "none", "nan", "<na>"])


def calcular_duplicados_clave(df: pd.DataFrame) -> int:
    """Calcula la cantidad de duplicados bajo la terna (Departamento, Municipio, Año_Num)."""
    return int(df.duplicated(subset=["Departamento", "Municipio", "Año_Num"], keep=False).sum())


def construir_tabla_descriptiva(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Construye la síntesis estadística paramétrica y no paramétrica de variables continuas."""
    filas = []
    for etiqueta, col in [
        ("IRCA General", "IRCA_Num"),
        ("IRCA Urbano", "IRCAurbano_Num"),
        ("IRCA Rural", "IRCArural_Num"),
    ]:
        s = dataframe[col].dropna()
        if s.empty:
            continue
        q1 = float(s.quantile(0.25))
        q3 = float(s.quantile(0.75))
        iqr = q3 - q1
        filas.append({
            "Variable": etiqueta,
            "Observaciones (N)": int(len(s)),
            "Faltantes (ND)": int(len(dataframe) - len(s)),
            "Media (x̄)": round(float(s.mean()), 2),
            "Desv. Estándar (s)": round(float(s.std()), 2),
            "Coef. Variación (%)": round(float(s.std() / s.mean() * 100), 2) if s.mean() != 0 else np.nan,
            "Mínimo": round(float(s.min()), 2),
            "Primer Cuartil (Q1)": round(q1, 2),
            "Mediana (Q2)": round(float(s.median()), 2),
            "Tercer Cuartil (Q3)": round(q3, 2),
            "Máximo": round(float(s.max()), 2),
            "Rango Intercuartílico (IQR)": round(iqr, 2),
            "Asimetría (Fisher)": round(float(stats.skew(s)), 3),
            "Curtosis (Exceso)": round(float(stats.kurtosis(s)), 3),
        })
    return pd.DataFrame(filas)


def evaluar_brecha_urbano_rural(s_rur: pd.Series, s_urb: pd.Series) -> str:
    """Evalúa cuantitativamente la diferencia de medianas entre el sector rural y urbano."""
    if not s_rur.empty and not s_urb.empty:
        med_rur = float(s_rur.median())
        med_urb = float(s_urb.median())
        dif_med = med_rur - med_urb
        if med_rur > med_urb:
            return f"La mediana rural supera a la urbana por {dif_med:.2f} puntos."
        elif med_rur < med_urb:
            return f"La mediana urbana supera a la rural por {abs(dif_med):.2f} puntos."
        else:
            return "Las medianas rural y urbana son iguales."
    return "Datos insuficientes para comparar las medianas rural y urbana."


def evaluar_asimetria(s_irca: pd.Series) -> str:
    """Evalúa la morfología de la distribución mediante el coeficiente de asimetría de Fisher."""
    if not s_irca.empty:
        skew_val = float(stats.skew(s_irca))
        if skew_val > 0.1:
            return "La distribución tiene cola hacia valores altos."
        elif skew_val < -0.1:
            return "La distribución tiene cola hacia valores bajos."
        else:
            return "La distribución es aproximadamente simétrica."
    return "No hay datos suficientes para describir la forma de la distribución."


def calcular_tabla_limites_atipicos(df_vis: pd.DataFrame) -> pd.DataFrame:
    """Genera la tabla de límites de Tukey (1.5 × IQR) y conteo de atípicos para cada variable continua."""
    limites_lista = []
    for nombre, col in [
        ("IRCA General", "IRCA_Num"),
        ("IRCA Urbano", "IRCAurbano_Num"),
        ("IRCA Rural", "IRCArural_Num"),
    ]:
        s = df_vis[col].dropna()
        if not s.empty:
            q1, q3, iqr, lim_inf, lim_sup = calcular_limites_iqr(s)
            atipicos_masc = (s < lim_inf) | (s > lim_sup)
            conteo_atip = int(atipicos_masc.sum())
            pct_atip = (conteo_atip / len(s)) * 100
            limites_lista.append({
                "Variable": nombre,
                "No Nulos Evaluados": len(s),
                "Q1 (25%)": round(q1, 2),
                "Q3 (75%)": round(q3, 2),
                "IQR": round(iqr, 2),
                "Límite Inferior (Tukey)": round(lim_inf, 2),
                "Límite Superior (Tukey)": round(lim_sup, 2),
                "Conteo Atípicos": conteo_atip,
                "Porcentaje Atípicos (%)": round(pct_atip, 2),
            })
    return pd.DataFrame(limites_lista)


def calcular_matriz_correlacion(df_vis: pd.DataFrame, metodo: str = "spearman") -> pd.DataFrame:
    """Calcula la matriz de correlación entre variables cuantitativas."""
    cols_cuant = ["IRCA_Num", "IRCAurbano_Num", "IRCArural_Num"]
    nombres_vis = ["IRCA General", "IRCA Urbano", "IRCA Rural"]
    df_sub_corr = df_vis[cols_cuant].copy()
    df_sub_corr.columns = nombres_vis
    return df_sub_corr.corr(method=metodo)


def calcular_metricas_recta_1_1(df_disp: pd.DataFrame) -> Dict[str, Any]:
    """Calcula conteos y porcentajes de contraste territorial respecto a la recta de identidad 1:1."""
    total_pares = len(df_disp)
    if total_pares == 0:
        return {
            "total_pares": 0,
            "rural_mayor": 0,
            "pct_rural_mayor": 0.0,
            "urbano_mayor": 0,
            "pct_urbano_mayor": 0.0,
            "iguales": 0,
            "pct_iguales": 0.0,
        }

    rural_mayor = int((df_disp["IRCArural_Num"] > df_disp["IRCAurbano_Num"]).sum())
    pct_rural_mayor = (rural_mayor / total_pares) * 100
    urbano_mayor = int((df_disp["IRCAurbano_Num"] > df_disp["IRCArural_Num"]).sum())
    pct_urbano_mayor = (urbano_mayor / total_pares) * 100
    iguales = int((df_disp["IRCArural_Num"] == df_disp["IRCAurbano_Num"]).sum())
    pct_iguales = (iguales / total_pares) * 100

    return {
        "total_pares": total_pares,
        "rural_mayor": rural_mayor,
        "pct_rural_mayor": pct_rural_mayor,
        "urbano_mayor": urbano_mayor,
        "pct_urbano_mayor": pct_urbano_mayor,
        "iguales": iguales,
        "pct_iguales": pct_iguales,
    }


def calcular_tendencia_anual(df_in: pd.DataFrame, mediana: bool = False) -> pd.DataFrame:
    """Calcula la agregación anual (media o mediana) del IRCA y sus componentes."""
    agrup = df_in.groupby("Año_Num")
    if mediana:
        res = agrup[["IRCA_Num", "IRCAurbano_Num", "IRCArural_Num"]].median().reset_index()
    else:
        res = agrup[["IRCA_Num", "IRCAurbano_Num", "IRCArural_Num"]].mean().reset_index()
    res["Conteo_Reportes"] = agrup["IRCA_Num"].count().values
    return res


def calcular_ranking_departamental(df_vis: pd.DataFrame, anio: int) -> pd.DataFrame:
    """Calcula el ranking departamental por promedio de IRCA para un año determinado."""
    df_ranking = (
        df_vis[df_vis["Año_Num"] == anio]
        .groupby("Departamento")["IRCA_Num"]
        .agg(["mean", "count"])
        .reset_index()
        .rename(columns={"mean": "IRCA_Promedio", "count": "Num_Municipios"})
        .sort_values("IRCA_Promedio", ascending=True)
    )
    if not df_ranking.empty:
        df_ranking["Nivel_Riesgo_Asignado"] = df_ranking["IRCA_Promedio"].apply(
            clasificar_riesgo_resolucion_2115
        )
    return df_ranking


def calcular_distribucion_riesgo_anual(df_vis: pd.DataFrame) -> pd.DataFrame:
    """Calcula la distribución porcentual anualizada de municipios en cada categoría de riesgo."""
    df_pct_riesgo = (
        df_vis.dropna(subset=["Año_Num", "NivelRiesgo_Recalculado"])
        .groupby(["Año_Num", "NivelRiesgo_Recalculado"])
        .size()
        .reset_index(name="Conteo")
    )
    if not df_pct_riesgo.empty:
        df_tot_por_anio = df_pct_riesgo.groupby("Año_Num")["Conteo"].transform("sum")
        df_pct_riesgo["Porcentaje"] = (df_pct_riesgo["Conteo"] / df_tot_por_anio) * 100
    return df_pct_riesgo

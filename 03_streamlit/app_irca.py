"""
========================================================================================
Aplicación de Análisis Exploratorio de Datos (EDA)
Calidad del Agua para Consumo Humano en Colombia (IRCA, SIVICAP - Instituto Nacional de Salud)
========================================================================================
Desarrollada para soporte de artículo científico universitario.
Cumple rigurosamente con los lineamientos de la Resolución 2115 de 2007 y estándares
metodológicos para el análisis riguroso de series de calidad sanitaria del agua.
"""

from scipy import stats
import pandas as pd
import streamlit as st

from src.carga import (
    cargar_datos_desde_postgres,
    obtener_conexion_postgres,
)
from src.limpieza import procesar_datos_irca
from src.analisis import (
    calcular_distribucion_riesgo_anual,
    calcular_duplicados_clave,
    calcular_matriz_correlacion,
    calcular_metricas_recta_1_1,
    calcular_ranking_departamental,
    calcular_tabla_limites_atipicos,
    calcular_tendencia_anual,
    construir_tabla_descriptiva,
    evaluar_asimetria,
    evaluar_brecha_urbano_rural,
    obtener_resumen_faltantes,
    obtener_resumen_tipos,
)
from src.graficos import (
    crear_boxplot_anual,
    crear_boxplot_urbano_rural,
    crear_grafico_distribucion_riesgo_apilado,
    crear_grafico_completitud,
    crear_grafico_lineas_tendencia,
    crear_grafico_medianas_anuales,
    crear_grafico_ranking_departamental,
    crear_histograma_frecuencias,
    crear_scatter_urbano_rural,
    mostrar_dataframe,
    mostrar_grafico,
)

# ======================================================================================
# CONFIGURACIÓN GENERAL DE LA APLICACIÓN STREAMLIT
# ======================================================================================
st.set_page_config(
    page_title="EDA IRCA Colombia - Calidad del Agua",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ======================================================================================
# CARGA INICIAL DE DATOS DESDE POSTGRESQL / NEON
# ======================================================================================
st.sidebar.markdown("## 🔍 Filtros")
tabla_remota = "irca"
try:
    cadena_pg = obtener_conexion_postgres()
    if not cadena_pg:
        st.error(
            "❌ **Error de configuración:** No se encontró la conexión a PostgreSQL. "
            "Configure `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` y `DB_NAME` "
            "bajo `[postgres]` en `.streamlit/secrets.toml`."
        )
        st.stop()

    tabla_remota = st.secrets.get("postgres", {}).get("table_name", tabla_remota)
    df_crudo = cargar_datos_desde_postgres(cadena_pg, tabla_remota)
except Exception as exc:
    st.sidebar.error("🔴 **Error en fuente activa:** PostgreSQL / Neon")
    st.error(
        f"❌ Error crítico al conectar o consultar PostgreSQL/Neon "
        f"(tabla: '{tabla_remota}'): {exc}"
    )
    st.stop()

# Procesamiento estandarizado y tipado sin mutación de registros originales
df_completo = procesar_datos_irca(df_crudo)
TOTAL_FILAS_ORIGINAL = len(df_completo)

# ======================================================================================
# CONTROLES Y FILTROS DE VISUALIZACIÓN EN BARRA LATERAL (REGLA 1)
# ======================================================================================
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Filtros de Visualización")

# Filtro de ámbito geográfico (Manejo de #TODOS según Regla 4)
opcion_ambito = st.sidebar.selectbox(
    "Ámbito territorial:",
    options=[
        "Solo municipales",
        "Solo consolidados departamentales (#TODOS)",
    ],
    index=0,
)

# Filtro por Departamento
lista_deptos = sorted([d for d in df_completo["Departamento"].dropna().unique()])
deptos_seleccionados = st.sidebar.multiselect(
    "Filtrar por Departamento:",
    options=lista_deptos,
    default=[],
    placeholder="Todos los departamentos",
)

# Filtro por Rango Temporal (Años)
anios_validos = sorted([int(a) for a in df_completo["Año_Num"].dropna().unique()])
if anios_validos:
    min_anio, max_anio = min(anios_validos), max(anios_validos)
    rango_anios = st.sidebar.slider(
        "Rango de Años:",
        min_value=min_anio,
        max_value=max_anio,
        value=(min_anio, max_anio),
        step=1,
    )
else:
    min_anio, max_anio = 0, 0
    rango_anios = (0, 0)

# Aplicar máscara lógica SOLO para visualización
mascara = pd.Series(True, index=df_completo.index)

if opcion_ambito == "Solo municipales":
    mascara &= ~df_completo["Es_Departamental"]
else:
    mascara &= df_completo["Es_Departamental"]

if deptos_seleccionados:
    mascara &= df_completo["Departamento"].isin(deptos_seleccionados)

mascara &= (df_completo["Año_Num"] >= rango_anios[0]) & (
    df_completo["Año_Num"] <= rango_anios[1]
)

df_vis = df_completo[mascara]

# Indicador de estado en barra lateral
st.sidebar.metric(
    "Registros Filtrados / Total",
    f"{len(df_vis):,} / {TOTAL_FILAS_ORIGINAL:,}".replace(",", "."),
    delta=f"{(len(df_vis) / TOTAL_FILAS_ORIGINAL * 100):.1f}% del total",
)

# ======================================================================================
# ENCABEZADO PRINCIPAL DE LA APLICACIÓN
# ======================================================================================
st.title("💧 Análisis Exploratorio de Datos (EDA): IRCA en Colombia")
st.markdown(
    """
    Explora y resume los datos del Índice de Riesgo de la Calidad del Agua (IRCA) en Colombia.
    Permite revisar su calidad, distribución, cambios en el tiempo y diferencias territoriales.
    """
)

# Métricas directas de resumen en cabecera
mcol1, mcol2, mcol3, mcol4, mcol5 = st.columns(5)
with mcol1:
    st.metric("Total Registros Originales", f"{TOTAL_FILAS_ORIGINAL:,}".replace(",", "."))
with mcol2:
    st.metric("Departamentos Monitoreados", df_completo["Departamento"].nunique())
with mcol3:
    n_mun = df_completo[~df_completo["Es_Departamental"]]["Municipio"].nunique()
    st.metric("Municipios Reportantes", n_mun)
with mcol4:
    st.metric("Filas Consolidadas (#TODOS)", int(df_completo["Es_Departamental"].sum()))
with mcol5:
    st.metric(
        "Periodo Histórico",
        f"{df_completo['Año_Num'].min()} - {df_completo['Año_Num'].max()}",
    )

st.markdown("---")

# ======================================================================================
# DEFINICIÓN DE PESTAÑAS (TABS) ANALÍTICAS
# ======================================================================================
tab_calidad, tab_desc, tab_dist, tab_atip, tab_corr, tab_tend, tab_dept = st.tabs([
    "📋 Calidad de Datos",
    "📊 Estadísticas Descriptivas",
    "📈 Distribuciones",
    "🎯 Valores Atípicos",
    "🔗 Correlaciones",
    "⏳ Tendencia Temporal",
    "🗺️ Departamentos y Riesgo",
])

# ======================================================================================
# PESTAÑA 1: CALIDAD DE DATOS
# ======================================================================================
with tab_calidad:
    st.subheader("Auditoría de Calidad, Integridad y Consistencia de Datos")

    col_q1, col_q2 = st.columns(2)

    with col_q1:
        st.markdown("#### Estructura y Tipado de Columnas")
        df_tipos = obtener_resumen_tipos(df_crudo, df_completo, min_anio, max_anio, bool(anios_validos))
        mostrar_dataframe(df_tipos, hide_index=True)

    with col_q2:
        st.markdown("#### Datos faltantes por columna (ND = no disponible)")
        df_faltantes = obtener_resumen_faltantes(df_crudo, TOTAL_FILAS_ORIGINAL)
        columnas_irca = ["IRCA", "IRCAurbano", "IRCArural"]
        etiquetas_irca = {
            "IRCA": "IRCA total",
            "IRCAurbano": "IRCA urbano",
            "IRCArural": "IRCA rural",
        }
        df_faltantes_irca = df_faltantes[
            df_faltantes["Variable"].isin(columnas_irca)
        ].copy()
        df_faltantes_irca["Variable"] = df_faltantes_irca["Variable"].map(etiquetas_irca)
        df_faltantes_irca = df_faltantes_irca.rename(
            columns={
                "Conteo Faltantes (ND/NULL)": "Sin dato (ND)",
                "Porcentaje (%)": "% sin dato",
                "Completitud (%)": "% con dato",
            }
        )[["Variable", "Sin dato (ND)", "% sin dato", "% con dato"]]
        mostrar_dataframe(df_faltantes_irca, hide_index=True)

    # Gráfico de barras de completitud
    st.markdown("#### Porcentaje de registros con dato")
    df_faltantes_grafico = df_faltantes[
        df_faltantes["Variable"].isin(columnas_irca)
    ].copy()
    df_faltantes_grafico["Variable"] = df_faltantes_grafico["Variable"].map(etiquetas_irca)
    fig_comp = crear_grafico_completitud(df_faltantes_grafico)
    mostrar_grafico(fig_comp)
    st.caption(
        "¿Cómo leerlo? Cada barra indica qué porcentaje de registros tiene dato. "
        "Una barra baja significa que esa variable se midió en pocos casos. "
        "Los datos faltantes no se rellenaron."
    )

    st.markdown("---")
    st.markdown("#### Duplicados y consolidados departamentales")
    dup_col1, dup_col2 = st.columns(2)

    with dup_col1:
        dups_clave = calcular_duplicados_clave(df_completo)
        st.metric(
            "Duplicados por (Departamento, Municipio, Año)",
            dups_clave,
            help="Verifica si un mismo municipio tiene más de un reporte registrado en el mismo año.",
        )
        if dups_clave > 0:
            st.warning(f"⚠️ Se detectaron {dups_clave} registros con claves repetidas.")

    with dup_col2:
        st.metric(
            "Consolidados Departamentales (#TODOS)",
            f"{int(df_completo['Es_Departamental'].sum())} filas ({df_completo['Es_Departamental'].mean()*100:.2f}%)",
            help="Registros agregados donde Municipio = '#TODOS', correspondientes a consolidados provinciales.",
        )

# ======================================================================================
# PESTAÑA 2: ESTADÍSTICAS DESCRIPTIVAS
# ======================================================================================
with tab_desc:
    st.subheader("Estadísticas Descriptivas y Morfología de las Distribuciones")

    s_irca = df_vis["IRCA_Num"].dropna()
    s_urb = df_vis["IRCAurbano_Num"].dropna()
    s_rur = df_vis["IRCArural_Num"].dropna()

    stat_c1, stat_c2, stat_c3 = st.columns(3)
    with stat_c1:
        st.markdown("##### 💧 IRCA General")
        st.metric("Media", f"{s_irca.mean():.2f}" if not s_irca.empty else "N/A")
        st.metric("Mediana (P50)", f"{s_irca.median():.2f}" if not s_irca.empty else "N/A")
        st.metric("Desv. Estándar", f"{s_irca.std():.2f}" if not s_irca.empty else "N/A")
        st.metric("Asimetría (Skewness)", f"{stats.skew(s_irca):.2f}" if not s_irca.empty else "N/A")
        st.metric("Curtosis", f"{stats.kurtosis(s_irca):.2f}" if not s_irca.empty else "N/A")

    with stat_c2:
        st.markdown("##### 🏙️ IRCA Urbano")
        st.metric("Media", f"{s_urb.mean():.2f}" if not s_urb.empty else "N/A")
        st.metric("Mediana (P50)", f"{s_urb.median():.2f}" if not s_urb.empty else "N/A")
        st.metric("Desv. Estándar", f"{s_urb.std():.2f}" if not s_urb.empty else "N/A")
        st.metric("Asimetría (Skewness)", f"{stats.skew(s_urb):.2f}" if not s_urb.empty else "N/A")
        st.metric("Curtosis", f"{stats.kurtosis(s_urb):.2f}" if not s_urb.empty else "N/A")

    with stat_c3:
        st.markdown("##### 🌾 IRCA Rural")
        st.metric("Media", f"{s_rur.mean():.2f}" if not s_rur.empty else "N/A")
        st.metric("Mediana (P50)", f"{s_rur.median():.2f}" if not s_rur.empty else "N/A")
        st.metric("Desv. Estándar", f"{s_rur.std():.2f}" if not s_rur.empty else "N/A")
        st.metric("Asimetría (Skewness)", f"{stats.skew(s_rur):.2f}" if not s_rur.empty else "N/A")
        st.metric("Curtosis", f"{stats.kurtosis(s_rur):.2f}" if not s_rur.empty else "N/A")

    st.markdown("---")
    st.markdown("#### Resumen estadístico")
    df_stats_tabla = construir_tabla_descriptiva(df_vis)
    mostrar_dataframe(df_stats_tabla, hide_index=True)

    with st.expander("¿Cómo leer esta tabla?"):
        st.markdown(
            """
            - **N:** cantidad de observaciones disponibles.
            - **Faltantes:** registros sin dato para esa variable.
            - **Media:** promedio de los valores.
            - **Mediana:** valor central al ordenar los datos.
            - **Q1 / Q3:** valores que dejan por debajo el 25 % y el 75 % de las observaciones.
            - **IQR:** distancia entre Q1 y Q3; resume la dispersión central.
            - **Coeficiente de variación:** dispersión relativa respecto a la media.
            - **Asimetría:** indica hacia qué lado se alarga la distribución.
            - **Curtosis:** describe el peso de las colas respecto a una forma de referencia.
            """
        )

    texto_brecha = evaluar_brecha_urbano_rural(s_rur, s_urb)
    texto_asimetria = evaluar_asimetria(s_irca)

    st.markdown(
        f"""
        > **Interpretación calculada para la selección actual:**
        > - **Medianas:** {texto_brecha}
        > - **Cola de la distribución:** {texto_asimetria}
        """
    )

# ======================================================================================
# PESTAÑA 3: DISTRIBUCIONES
# ======================================================================================
with tab_dist:
    st.subheader("Análisis de Distribuciones Empíricas")

    var_dist_opciones = {
        "IRCA General": "IRCA_Num",
        "IRCA Urbano": "IRCAurbano_Num",
        "IRCA Rural": "IRCArural_Num",
    }

    col_ctrl1, col_ctrl2 = st.columns([1, 1])
    with col_ctrl1:
        sel_var_nombre = st.selectbox("Seleccione la variable a graficar:", list(var_dist_opciones.keys()), index=0)
        sel_var_col = var_dist_opciones[sel_var_nombre]
    with col_ctrl2:
        num_bins = st.slider("Número de intervalos (bins):", min_value=10, max_value=60, value=30, step=5)

    serie_dist = df_vis[sel_var_col].dropna()

    if not serie_dist.empty:
        col_graf1, col_graf2 = st.columns(2)
        with col_graf1:
            st.markdown(f"##### Histograma de Frecuencias: {sel_var_nombre}")
            fig_hist = crear_histograma_frecuencias(df_vis, sel_var_col, sel_var_nombre, num_bins)
            mostrar_grafico(fig_hist)

        with col_graf2:
            st.markdown("##### Diagrama de Caja Comparativo: Urbano vs Rural")
            fig_box_comp = crear_boxplot_urbano_rural(df_vis)
            mostrar_grafico(fig_box_comp)
    else:
        st.warning("No hay suficientes datos no nulos en el subconjunto seleccionado para graficar distribuciones.")

# ======================================================================================
# PESTAÑA 4: VALORES ATÍPICOS
# ======================================================================================
with tab_atip:
    st.subheader("Detección y Caracterización de Valores Atípicos (Regla 1.5 × IQR)")

    df_limites = calcular_tabla_limites_atipicos(df_vis)
    st.markdown("#### Detección de valores atípicos (método de Tukey)")
    mostrar_dataframe(df_limites, hide_index=True)
    with st.expander("¿Cómo leer esta tabla?"):
        st.write(
            "Q1 y Q3 son los valores que dejan por debajo al 25 % y al 75 % de los datos. "
            "IQR es la distancia entre ambos. Un valor es atípico si está por debajo de "
            "Q1 − 1,5 × IQR o por encima de Q3 + 1,5 × IQR. En el IRCA importa el límite "
            "superior: un registro por encima es un municipio con riesgo inusualmente alto. "
            "Los atípicos no se eliminan."
        )

    atipicos_zonales = df_limites.set_index("Variable")
    resumen_atipicos_zonales = []
    for zona, variable in [("urbano", "IRCA Urbano"), ("rural", "IRCA Rural")]:
        if variable in atipicos_zonales.index:
            fila = atipicos_zonales.loc[variable]
            resumen_atipicos_zonales.append(
                f"IRCA {zona}: {int(fila['Conteo Atípicos']):,} registros "
                f"({fila['Porcentaje Atípicos (%)']:.2f}%).".replace(",", ".")
            )
    if resumen_atipicos_zonales:
        st.caption(" ".join(resumen_atipicos_zonales))

    st.markdown("---")
    st.markdown("#### Boxplots Anuales de IRCA con Identificación de Atípicos")
    fig_box_anio = crear_boxplot_anual(df_vis)
    mostrar_grafico(fig_box_anio)
    st.caption("Cada caja muestra el rango central del IRCA de ese año; los puntos señalan valores alejados.")

    with st.expander("🔍 Explorar registros clasificados como atípicos en IRCA General"):
        filas_atip = df_vis[df_vis["Atipico_IRCA"]][
            ["Departamento", "Municipio", "Año_Num", "IRCA_Num", "NivelRiesgo_Recalculado", "IRCAurbano_Num", "IRCArural_Num"]
        ]
        st.write(f"Mostrando {len(filas_atip)} registros atípicos (conservados íntegramente en el dataset):")
        mostrar_dataframe(filas_atip)

# ======================================================================================
# PESTAÑA 5: CORRELACIONES
# ======================================================================================
with tab_corr:
    st.subheader("Estructura de Correlación y Relación Urbano-Rural")

    matriz_corr = calcular_matriz_correlacion(df_vis, metodo="spearman")
    pares_correlacion = [
        ("IRCA total y urbano", "IRCA_Num", "IRCAurbano_Num", "IRCA General", "IRCA Urbano"),
        ("IRCA total y rural", "IRCA_Num", "IRCArural_Num", "IRCA General", "IRCA Rural"),
        ("IRCA urbano y rural", "IRCAurbano_Num", "IRCArural_Num", "IRCA Urbano", "IRCA Rural"),
    ]
    tarjetas_corr = st.columns(3)
    for tarjeta, (etiqueta, columna_a, columna_b, variable_a, variable_b) in zip(
        tarjetas_corr, pares_correlacion
    ):
        registros_completos = df_vis[[columna_a, columna_b]].dropna()
        valor_corr = matriz_corr.loc[variable_a, variable_b]
        fuerza = (
            "fuerte" if abs(valor_corr) >= 0.7
            else "moderada" if abs(valor_corr) >= 0.4
            else "débil"
        ) if pd.notna(valor_corr) else "no calculable"
        tarjeta.metric(
            etiqueta,
            f"{valor_corr:.2f}" if pd.notna(valor_corr) else "N/A",
            delta=f"{fuerza} · {len(registros_completos):,} registros".replace(",", "."),
            delta_color="off",
        )

    st.caption(
        "¿Cómo leerlo? Va de -1 a 1. Cerca de 1: cuando una variable sube, la otra también. "
        "Cerca de 0: no hay relación. Solo se usan los registros que tienen ambos datos."
    )

    col_corr1, col_corr2 = st.columns([1, 1])

    with col_corr2:
        st.markdown("##### Dispersión: IRCA Urbano vs IRCA Rural")
        df_disp = df_vis.dropna(subset=["IRCAurbano_Num", "IRCArural_Num"]).copy()

        if not df_disp.empty:
            fig_scatter = crear_scatter_urbano_rural(df_disp)
            mostrar_grafico(fig_scatter)

            metricas_1_1 = calcular_metricas_recta_1_1(df_disp)
            unidad_dispersion = (
                "los municipios"
                if opcion_ambito == "Solo municipales"
                else "los consolidados departamentales"
            )
            st.caption(
                f"¿Cómo leerlo? Solo aparecen {unidad_dispersion} con ambos datos disponibles; "
                f"el {metricas_1_1['pct_rural_mayor']:.1f}% queda por encima de la recta 1:1 "
                "(IRCA rural mayor que el urbano)."
            )
        else:
            st.warning("No hay suficientes pares simultáneos urbano-rural en el filtro actual.")

    with col_corr1:
        st.markdown("##### Medianas urbanas y rurales por año")
        df_medianas = calcular_tendencia_anual(df_vis, mediana=True)
        fig_medianas = crear_grafico_medianas_anuales(df_medianas)
        mostrar_grafico(fig_medianas)
        st.caption("Cada barra muestra la mediana de la zona en ese año; los municipios que reportan pueden variar entre años.")

# ======================================================================================
# PESTAÑA 6: TENDENCIA TEMPORAL
# ======================================================================================
with tab_tend:
    anios_vis_serie = df_vis["Año_Num"].dropna()
    rango_vis_str = (
        f"{int(anios_vis_serie.min())} - {int(anios_vis_serie.max())}"
        if not anios_vis_serie.empty
        else (f"{min_anio} - {max_anio}" if anios_validos else "")
    )
    st.subheader(f"Evolución Temporal del Índice de Riesgo ({rango_vis_str})")

    metrica_agregada = st.radio(
        "Estadístico de agregación anual:",
        options=["Media (Promedio aritmético)", "Mediana (Robusta ante atípicos)"],
        horizontal=True,
    )
    usar_mediana = "Mediana" in metrica_agregada

    df_tendencia = calcular_tendencia_anual(df_vis, usar_mediana)

    if not df_tendencia.empty:
        fig_lineas = crear_grafico_lineas_tendencia(
            df_tendencia,
            metrica_agregada.split(' ')[0],
            rango_vis_str,
        )
        mostrar_grafico(fig_lineas)
        st.caption("La lista de municipios que reportan puede cambiar cada año.")

        st.markdown("#### Tabla de Agregación Histórica Anual")
        df_tend_tabla = df_tendencia.copy()
        df_tend_tabla.columns = ["Año", "IRCA General", "IRCA Urbano", "IRCA Rural", "Municipios Reportantes"]
        mostrar_dataframe(df_tend_tabla.round(2), hide_index=True)

# ======================================================================================
# PESTAÑA 7: DEPARTAMENTOS Y RIESGO
# ======================================================================================
with tab_dept:
    st.subheader("Desagregación Territorial y Distribución de Riesgo Normativo")

    col_dep_ctrl1, col_dep_ctrl2 = st.columns([1, 1])
    with col_dep_ctrl1:
        anios_dept_disp = sorted([int(a) for a in df_vis["Año_Num"].dropna().unique()])
        anio_ranking = st.selectbox(
            "Seleccionar año para Ranking Departamental:",
            options=anios_dept_disp,
            index=len(anios_dept_disp) - 1 if anios_dept_disp else 0,
        )

    df_ranking = calcular_ranking_departamental(df_vis, anio_ranking)

    if not df_ranking.empty:
        st.markdown(f"#### Ranking Departamental por IRCA Promedio en el Año {anio_ranking}")
        fig_rank = crear_grafico_ranking_departamental(df_ranking, anio_ranking)
        mostrar_grafico(fig_rank)

    st.markdown("---")
    st.markdown("#### Distribución Porcentual del Nivel de Riesgo por Año (100% Apilado)")

    df_pct_riesgo = calcular_distribucion_riesgo_anual(df_vis)
    fig_stack = crear_grafico_distribucion_riesgo_apilado(df_pct_riesgo)
    mostrar_grafico(fig_stack)

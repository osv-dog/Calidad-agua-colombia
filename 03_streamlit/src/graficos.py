"""
Módulo de construcción de gráficos interactivos (Plotly) y funciones de visualización.
"""

from typing import Dict, List
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Paleta cromática oficial normalizada para niveles de riesgo (Resolución 2115 de 2007)
PALETA_RIESGO: Dict[str, str] = {
    "Sin riesgo": "#27ae60",               # Verde sanitario
    "Riesgo bajo": "#f39c12",              # Amarillo / ámbar
    "Riesgo medio": "#e67e22",             # Naranja preventivo
    "Riesgo alto": "#e74c3c",              # Rojo crítico
    "Inviable sanitariamente": "#8e44ad",  # Púrpura sanitario de alarma máxima
    "No Disponible": "#95a5a6",            # Gris neutro para valores sin dato
}

ORDEN_RIESGO: List[str] = [
    "Sin riesgo",
    "Riesgo bajo",
    "Riesgo medio",
    "Riesgo alto",
    "Inviable sanitariamente",
]


def mostrar_dataframe(df: pd.DataFrame, **kwargs) -> None:
    """Renderiza un dataframe en Streamlit adaptándose a la versión instalada."""
    try:
        st.dataframe(df, width="stretch", **kwargs)
    except TypeError:
        st.dataframe(df, use_container_width=True, **kwargs)


def mostrar_grafico(fig: go.Figure, **kwargs) -> None:
    """Renderiza una figura Plotly en Streamlit adaptándose a la versión instalada."""
    try:
        st.plotly_chart(fig, width="stretch", **kwargs)
    except TypeError:
        st.plotly_chart(fig, use_container_width=True, **kwargs)


def crear_grafico_completitud(df_faltantes: pd.DataFrame) -> go.Figure:
    """Genera barras horizontales apiladas con porcentajes de datos presentes y faltantes."""
    fig_comp = go.Figure()
    fig_comp.add_trace(go.Bar(
        x=df_faltantes["Completitud (%)"],
        y=df_faltantes["Variable"],
        name="Con dato",
        orientation="h",
        marker_color="#2878B5",
        text=df_faltantes["Completitud (%)"],
        texttemplate="%{text:.1f}%",
        textposition="inside",
        insidetextanchor="middle",
    ))
    fig_comp.add_trace(go.Bar(
        x=df_faltantes["Porcentaje (%)"],
        y=df_faltantes["Variable"],
        name="Sin dato (ND)",
        orientation="h",
        marker_color="#D9DEE5",
        text=df_faltantes["Porcentaje (%)"],
        texttemplate="%{text:.1f}%",
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(color="#333333"),
    ))
    fig_comp.update_layout(
        barmode="stack",
        height=250,
        title=None,
        xaxis=dict(range=[0, 100], ticksuffix="%", title=None),
        yaxis=dict(title=None, autorange="reversed"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        margin=dict(l=20, r=20, t=35, b=20),
    )
    return fig_comp


def crear_histograma_frecuencias(
    df_vis: pd.DataFrame,
    sel_var_col: str,
    sel_var_nombre: str,
    num_bins: int = 30,
) -> go.Figure:
    """Genera histograma de frecuencias con líneas de referencia de umbrales normativos."""
    fig_hist = px.histogram(
        df_vis,
        x=sel_var_col,
        nbins=num_bins,
        marginal="rug",
        title=f"Distribución empírica de {sel_var_nombre}",
        labels={sel_var_col: "Puntaje IRCA (0 - 100)"},
        color_discrete_sequence=["#2980b9"],
    )
    fig_hist.add_vline(x=5.0, line_dash="dash", line_color="#27ae60", annotation_text="Sin riesgo (5%)")
    fig_hist.add_vline(x=35.0, line_dash="dash", line_color="#e67e22", annotation_text="Riesgo alto (35%)")
    fig_hist.add_vline(x=80.0, line_dash="dash", line_color="#8e44ad", annotation_text="Inviable (80%)")
    fig_hist.update_layout(height=420, margin=dict(l=20, r=20, t=40, b=30))
    return fig_hist


def crear_boxplot_urbano_rural(df_vis: pd.DataFrame) -> go.Figure:
    """Genera diagrama de caja comparativo entre IRCA Urbano y Rural."""
    df_long = df_vis.melt(
        id_vars=["Departamento", "Municipio", "Año_Num"],
        value_vars=["IRCAurbano_Num", "IRCArural_Num"],
        var_name="Ámbito",
        value_name="Valor_IRCA",
    ).dropna(subset=["Valor_IRCA"])
    df_long["Ámbito"] = df_long["Ámbito"].map({
        "IRCAurbano_Num": "Urbano",
        "IRCArural_Num": "Rural",
    })

    fig_box_comp = px.box(
        df_long,
        x="Ámbito",
        y="Valor_IRCA",
        color="Ámbito",
        points="outliers",
        color_discrete_map={"Urbano": "#3498db", "Rural": "#e67e22"},
        title="Contraste de dispersión y medianas: IRCA Urbano vs Rural",
        labels={"Valor_IRCA": "Puntaje IRCA"},
    )
    fig_box_comp.add_hline(y=5.0, line_dash="dot", line_color="#27ae60", annotation_text="Límite Sin Riesgo")
    fig_box_comp.update_layout(height=420, showlegend=False, margin=dict(l=20, r=20, t=40, b=30))
    return fig_box_comp


def crear_boxplot_anual(df_vis: pd.DataFrame) -> go.Figure:
    """Genera diagramas de caja anuales para evaluar la dispersión histórica y atípicos."""
    df_box_anio = df_vis.dropna(subset=["Año_Num", "IRCA_Num"]).sort_values("Año_Num")
    df_box_anio["Año_Str"] = df_box_anio["Año_Num"].astype(str)

    fig_box_anio = px.box(
        df_box_anio,
        x="Año_Str",
        y="IRCA_Num",
        points="outliers",
        color_discrete_sequence=["#16a085"],
        title="Evolución anual de la dispersión del IRCA y puntos atípicos (outliers)",
        labels={"Año_Str": "Año", "IRCA_Num": "IRCA General"},
    )
    fig_box_anio.add_hline(y=5.0, line_dash="dash", line_color="#27ae60", annotation_text="Sin Riesgo")
    fig_box_anio.update_layout(height=450, margin=dict(l=20, r=20, t=40, b=40))
    return fig_box_anio


def crear_scatter_urbano_rural(df_disp: pd.DataFrame) -> go.Figure:
    """Genera diagrama de dispersión IRCA Urbano vs Rural contra la recta de identidad 1:1."""
    fig_scatter = px.scatter(
        df_disp,
        x="IRCAurbano_Num",
        y="IRCArural_Num",
        color="NivelRiesgo_Recalculado",
        color_discrete_map=PALETA_RIESGO,
        hover_data=["Departamento", "Municipio", "Año_Num"],
        title="IRCA Urbano (Eje X) vs IRCA Rural (Eje Y)",
        labels={
            "IRCAurbano_Num": "IRCA Urbano",
            "IRCArural_Num": "IRCA Rural",
            "NivelRiesgo_Recalculado": "Nivel de Riesgo Global",
        },
        opacity=0.65,
    )
    # Recta de identidad 1:1
    fig_scatter.add_shape(
        type="line",
        x0=0,
        y0=0,
        x1=100,
        y1=100,
        line=dict(color="black", dash="dash", width=1.5),
    )
    fig_scatter.add_annotation(
        x=70,
        y=78,
        text="Recta 1:1 (Igualdad Urbano = Rural)",
        showarrow=False,
        font=dict(size=10, color="black"),
    )
    fig_scatter.update_layout(height=420, margin=dict(l=20, r=20, t=40, b=20))
    return fig_scatter


def crear_grafico_lineas_tendencia(
    df_tendencia: pd.DataFrame,
    metrica_nombre: str,
    rango_str: str,
) -> go.Figure:
    """Genera gráfico multilínea de la evolución anual del IRCA general, urbano y rural."""
    fig_lineas = go.Figure()

    fig_lineas.add_trace(go.Scatter(
        x=df_tendencia["Año_Num"],
        y=df_tendencia["IRCA_Num"],
        mode="lines+markers",
        name="IRCA General",
        line=dict(color="#2980b9", width=3),
        marker=dict(size=8),
    ))
    fig_lineas.add_trace(go.Scatter(
        x=df_tendencia["Año_Num"],
        y=df_tendencia["IRCAurbano_Num"],
        mode="lines+markers",
        name="IRCA Urbano",
        line=dict(color="#27ae60", width=2.5, dash="dash"),
        marker=dict(size=7),
    ))
    fig_lineas.add_trace(go.Scatter(
        x=df_tendencia["Año_Num"],
        y=df_tendencia["IRCArural_Num"],
        mode="lines+markers",
        name="IRCA Rural",
        line=dict(color="#e67e22", width=2.5, dash="dot"),
        marker=dict(size=7),
    ))

    # Línea de umbral sanitario de seguridad
    fig_lineas.add_hline(
        y=5.0,
        line_dash="dot",
        line_color="#27ae60",
        annotation_text="Límite 'Sin riesgo' (5%)",
    )

    fig_lineas.update_layout(
        title=f"Evolución anual de {metrica_nombre} del IRCA ({rango_str})",
        xaxis_title="Año de Monitoreo",
        yaxis_title=f"{metrica_nombre} del IRCA (0 - 100)",
        height=460,
        xaxis=dict(dtick=1),
        margin=dict(l=20, r=20, t=50, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig_lineas


def crear_grafico_medianas_anuales(df_tendencia: pd.DataFrame) -> go.Figure:
    """Compara las medianas urbana y rural de cada año con barras agrupadas."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_tendencia["Año_Num"],
        y=df_tendencia["IRCAurbano_Num"],
        name="Urbano",
        marker_color="#27ae60",
    ))
    fig.add_trace(go.Bar(
        x=df_tendencia["Año_Num"],
        y=df_tendencia["IRCArural_Num"],
        name="Rural",
        marker_color="#e67e22",
    ))
    fig.update_layout(
        title="Mediana anual del IRCA urbano y rural",
        xaxis_title="Año",
        yaxis_title="Mediana del IRCA (0 - 100)",
        barmode="group",
        height=430,
        xaxis=dict(dtick=1),
        margin=dict(l=20, r=20, t=50, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def crear_grafico_ranking_departamental(df_ranking: pd.DataFrame, anio: int) -> go.Figure:
    """Genera gráfico de barras horizontales del ranking departamental de calidad de agua."""
    fig_rank = px.bar(
        df_ranking,
        x="IRCA_Promedio",
        y="Departamento",
        orientation="h",
        color="Nivel_Riesgo_Asignado",
        color_discrete_map=PALETA_RIESGO,
        category_orders={"Nivel_Riesgo_Asignado": ORDEN_RIESGO},
        text="IRCA_Promedio",
        title=f"IRCA Promedio por Departamento ({anio}) - Ordenado de menor a mayor riesgo",
        labels={"IRCA_Promedio": "IRCA Promedio", "Departamento": "Departamento"},
        height=max(500, len(df_ranking) * 22),
    )
    fig_rank.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig_rank.update_layout(margin=dict(l=20, r=20, t=40, b=30))
    return fig_rank


def crear_grafico_distribucion_riesgo_apilado(df_pct_riesgo: pd.DataFrame) -> go.Figure:
    """Genera gráfico de barras 100% apiladas de la evolución temporal del riesgo normativo."""
    fig_stack = px.bar(
        df_pct_riesgo,
        x="Año_Num",
        y="Porcentaje",
        color="NivelRiesgo_Recalculado",
        color_discrete_map=PALETA_RIESGO,
        category_orders={"NivelRiesgo_Recalculado": ORDEN_RIESGO},
        title="Distribución Porcentual del Nivel de Riesgo Sanitario por Año (%)",
        labels={"Año_Num": "Año", "Porcentaje": "Porcentaje (%)", "NivelRiesgo_Recalculado": "Nivel de Riesgo"},
    )
    fig_stack.update_layout(
        barmode="stack",
        height=450,
        xaxis=dict(dtick=1),
        margin=dict(l=20, r=20, t=40, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig_stack

# Calidad del Agua para Consumo Humano en Colombia (IRCA)
Proyecto final - Minería de Datos (Electiva IV)

## Integrantes
- Cristian Márquez (MarquezCristiaa)
- Osvaldo Ospino (osv-dog)

## Estructura del repositorio
| Carpeta | Contenido |
|---|---|
| 01_datos/ | CSV original (`irca.csv`, no se modifica) |
| 02_sql/ | Scripts de PostgreSQL (Neon) y carga de datos |
| 03_streamlit/ | App de EDA en Python + Streamlit |
| 04_powerbi/ | Tablero de Power BI (`calidad_agua_irca.pbix`) |
| 05_articulo/ | Artículo, referencias y figuras (capturas) |

## Base de datos (Neon)
Orden de los scripts en `02_sql/`:
1. `01_crear_tablas.sql`: crea `irca_raw` (copia fiel del CSV, todo texto) e `irca` (tipos correctos).
2. `cargar_raw.py`: carga el CSV a `irca_raw`. Requiere un archivo `.env` con `NEON_URL` (ver `.env.example`).
3. `03_limpiar_datos.sql`: llena `irca` desde `irca_raw` (ND a nulo, año numérico, etiquetas unificadas).
4. `02_verificacion.sql`: consultas de verificación (19.160 filas en ambas tablas).

## Ejecutar la app de Streamlit
Las instrucciones completas están en [`03_streamlit/README.md`](03_streamlit/README.md). Resumen:
1. `python -m venv venv` y activarlo (`venv\Scripts\activate` en Windows).
2. `cd 03_streamlit` y `pip install -r requirements.txt`.
3. Copiar `.streamlit/secrets.toml.example` a `.streamlit/secrets.toml` y completar los datos de conexión a Neon.
4. `streamlit run app_irca.py`

## Power BI
Abrir `04_powerbi/calidad_agua_irca.pbix`, usar **Inicio > Actualizar** y, si lo pide, ingresar las credenciales de Neon (pestaña Base de datos).

## Fuente de datos
Portal Nacional de Datos Abiertos (datos.gov.co), conjunto nxt2-39c3.
Fecha de descarga: 30/10/2026

## Seguridad
Las credenciales no se suben al repositorio: `.env` y `.streamlit/secrets.toml` están en `.gitignore`.
# Calidad del Agua para Consumo Humano en Colombia (IRCA)
Proyecto final - Minería de Datos (Electiva IV)

## Integrantes
- Nombre 1 (usuario GitHub)
- Nombre 2 (usuario GitHub)

## Estructura del repositorio
| Carpeta | Contenido |
|---|---|
| 01_datos/ | CSV original (NO modificar) |
| 02_sql/ | Scripts PostgreSQL (Neon) |
| 03_streamlit/ | App de EDA en Python + Streamlit |
| 04_powerbi/ | Archivo .pbix |
| 05_evidencias/ | Capturas numeradas por herramienta (sin credenciales) |
| 06_articulo/ | Artículo Word y control de referencias |
| 07_bitacora/ | Decisiones, hallazgos y cronograma |

## Cómo ejecutar la app de Streamlit
1. `python -m venv venv`
2. Activar: `venv\Scripts\activate` (Windows) o `source venv/bin/activate` (Linux/Mac)
3. `pip install -r 03_streamlit/requirements.txt`
4. Copiar `.env.example` a `.env` y completar la cadena de conexión de Neon
5. `streamlit run 03_streamlit/app.py`

## Fuente de datos
Portal Nacional de Datos Abiertos (datos.gov.co), conjunto nxt2-39c3.
Fecha de descarga: ___/___/2026

# Análisis Exploratorio de Datos (EDA) - IRCA Colombia 💧

Aplicación interactiva en **Streamlit** para el análisis exploratorio y descriptivo del conjunto de datos *"Calidad del Agua para Consumo Humano en Colombia"* (IRCA, SIVICAP - Instituto Nacional de Salud). Desarrollada como soporte analítico para un artículo científico universitario, siguiendo las disposiciones técnicas de la **Resolución 2115 de 2007**.

---

## 🚀 Requisitos e Instalación

### 1. Activar el entorno virtual existente
El proyecto utiliza el entorno virtual ubicado en la carpeta `venv/`:

```bash
# En Linux / macOS:
source venv/bin/activate

# En Windows (PowerShell):
.\venv\Scripts\Activate.ps1
```

*(Si no existiera ningún entorno, se crearía con `python -m venv .venv`).*

### 2. Instalar dependencias
Dentro del entorno virtual activado:

```bash
pip install -r requirements.txt
```

---

## ▶️ Ejecución de la Aplicación

Para iniciar el servidor de Streamlit con el Python del entorno:

```bash
# Con el entorno virtual activado:
streamlit run app_irca.py

# O directamente desde la ruta del ejecutable:
venv/bin/streamlit run app_irca.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`.

---

## 🗄️ Conexión a PostgreSQL (Neon)

La aplicación obtiene los datos directamente de una tabla en Neon. Los parámetros
de conexión se guardan por separado en `.streamlit/secrets.toml`, no en `app_irca.py`,
así puedes cambiarlos sin editar el código.

En PowerShell, desde la carpeta del proyecto, crea el archivo local de configuración:

```powershell
New-Item -ItemType Directory -Force .streamlit
Copy-Item .streamlit\secrets.toml.example .streamlit\secrets.toml
```

Edita `.streamlit/secrets.toml` con los datos que aparecen en la conexión de Neon:

```toml
[postgres]
DB_USER = "usuario"
DB_PASSWORD = "contraseña"
DB_HOST = "host-de-neon"
DB_PORT = "5432"
DB_NAME = "nombre_base"
DB_SSLMODE = "require"
table_name = "irca"
```

Puedes cambiar cada valor de conexión en ese archivo cuando sea necesario. `table_name`
debe coincidir con el nombre real de la tabla.

La tabla `irca` debe contener las columnas `departamento_codigo`, `Departamento`,
`municipio_codigo`, `Municipio`, `anio`, `es_agregado_departamental`, `IRCA`,
`nivel_riesgo`, `irca_urbano`, `nivel_riesgo_urbano`, `irca_rural` y
`nivel_riesgo_rural`. La aplicación renombra estas columnas durante la carga para
adaptarlas a los nombres internos. Si cambias el nombre de la tabla, actualiza `table_name`.

`.streamlit/secrets.toml` está excluido de Git para no publicar credenciales. Para iniciar:

```powershell
python -m streamlit run app_irca.py
```

La aplicación usa PostgreSQL/Neon como única fuente de datos.

---

## 📑 Estructura de Pestañas Analíticas

1. **📋 Calidad de datos**: Estructura, tipos, faltantes (`ND` sin imputar) y unicidad por `(Departamento, Municipio, Año)`.
2. **📊 Estadísticas descriptivas**: Media, desviación estándar, mediana, cuartiles, asimetría de Fisher-Pearson y curtosis.
3. **📈 Distribuciones**: Histogramas con selector de intervalos y diagramas de caja (boxplots) comparativos entre zonas urbana y rural.
4. **🎯 Valores atípicos**: Límites robustos de Tukey (1,5 × IQR), conteos por variable y boxplots anuales (sin eliminar ningún registro).
5. **🔗 Correlaciones**: Tres correlaciones Spearman con conteos de pares completos, dispersión urbano-rural con recta 1:1 y barras agrupadas de medianas urbanas y rurales por año.
6. **⏳ Tendencia temporal**: Evolución histórica anual (2007-2024) del IRCA promedio y mediana con conteo de cobertura municipal.
7. **🗺️ Departamentos y riesgo**: Ranking departamental por año y distribución porcentual apilada del nivel de riesgo según Resolución 2115 de 2007.

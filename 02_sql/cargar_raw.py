"""
Carga el CSV original (sin modificarlo) en la tabla irca_raw de PostgreSQL (Neon).
Todo se guarda como texto, tal como viene en el archivo.
Uso:  python 02_sql/cargar_raw.py
"""
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

RAIZ = Path(__file__).resolve().parent.parent
CSV = RAIZ / "01_datos" / "irca.csv"

load_dotenv(RAIZ / ".env")
url = os.getenv("NEON_URL")
if not url:
    raise SystemExit("No se encontró NEON_URL. Revisa que exista el archivo .env en la carpeta del proyecto.")

# keep_default_na=False evita que valores como "ND" o "NA" se conviertan en nulos
df = pd.read_csv(CSV, dtype=str, keep_default_na=False, encoding="utf-8")
print(f"Filas leídas del CSV: {len(df)}  |  Columnas: {df.shape[1]}")

# Se asignan los nombres de columna de irca_raw por posición
df.columns = [
    "departamentocodigo", "departamento", "municipiocodigo", "municipio",
    "anio", "irca", "nivel_riesgo", "irca_urbano", "nivel_riesgo_urbano",
    "irca_rural", "nivel_riesgo_rural",
]

engine = create_engine(url)
with engine.begin() as conn:
    conn.execute(text("DELETE FROM irca_raw"))   # permite repetir el script sin duplicar
    df.to_sql("irca_raw", conn, if_exists="append", index=False,
              method="multi", chunksize=1000)

with engine.connect() as conn:
    en_bd = conn.execute(text("SELECT COUNT(*) FROM irca_raw")).scalar()

print(f"Filas en irca_raw (base de datos): {en_bd}")
print("VERIFICACIÓN OK: los conteos coinciden." if en_bd == len(df)
      else "ATENCIÓN: los conteos NO coinciden, avisar.")
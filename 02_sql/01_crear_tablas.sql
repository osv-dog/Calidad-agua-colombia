-- Proyecto: Calidad del agua para consumo humano en Colombia (IRCA)
-- Base de datos: PostgreSQL en Neon

-- TABLA 1: copia fiel del CSV, todo como texto (no se modifica ni se borra ningún registro)
CREATE TABLE IF NOT EXISTS irca_raw (
    departamentocodigo      TEXT,
    departamento            TEXT,
    municipiocodigo         TEXT,
    municipio               TEXT,
    anio                    TEXT,
    irca                    TEXT,
    nivel_riesgo            TEXT,
    irca_urbano             TEXT,
    nivel_riesgo_urbano     TEXT,
    irca_rural              TEXT,
    nivel_riesgo_rural      TEXT
);

-- TABLA 2: datos limpios con tipos correctos
CREATE TABLE IF NOT EXISTS irca (
    departamento_codigo       CHAR(2)       NOT NULL,
    departamento              VARCHAR(100)  NOT NULL,
    municipio_codigo          VARCHAR(6)    NOT NULL,
    municipio                 VARCHAR(100)  NOT NULL,
    anio                      SMALLINT      NOT NULL CHECK (anio BETWEEN 2007 AND 2024),
    es_agregado_departamental BOOLEAN       NOT NULL,
    irca                      NUMERIC(4,1)  NOT NULL CHECK (irca BETWEEN 0 AND 100),
    nivel_riesgo              VARCHAR(30)   NOT NULL,
    irca_urbano               NUMERIC(4,1)  CHECK (irca_urbano BETWEEN 0 AND 100),
    nivel_riesgo_urbano       VARCHAR(30),
    irca_rural                NUMERIC(4,1)  CHECK (irca_rural BETWEEN 0 AND 100),
    nivel_riesgo_rural        VARCHAR(30),
    PRIMARY KEY (departamento_codigo, municipio_codigo, anio)
);

-- Índices para acelerar los filtros más frecuentes
CREATE INDEX IF NOT EXISTS idx_irca_anio ON irca (anio);
CREATE INDEX IF NOT EXISTS idx_irca_departamento ON irca (departamento_codigo);
-- Limpieza: irca_raw (texto) -> irca (tipos correctos). No se elimina ningún registro.
DELETE FROM irca;   -- permite repetir el script sin duplicar

INSERT INTO irca (
    departamento_codigo, departamento, municipio_codigo, municipio, anio,
    es_agregado_departamental, irca, nivel_riesgo,
    irca_urbano, nivel_riesgo_urbano, irca_rural, nivel_riesgo_rural)
SELECT
    departamentocodigo,
    CASE WHEN departamentocodigo = '88'
         THEN 'Archipiélago de San Andrés, Providencia y Santa Catalina'
         ELSE departamento END,
    municipiocodigo,
    municipio,
    REPLACE(anio, ',', '')::SMALLINT,
    (municipiocodigo = '#TODOS'),
    irca::NUMERIC(4,1),
    CASE nivel_riesgo
        WHEN 'Riesgo alto' THEN 'Alto riesgo'
        WHEN 'Riesgo bajo' THEN 'Bajo riesgo'
        ELSE nivel_riesgo END,
    NULLIF(NULLIF(irca_urbano, 'ND'), '')::NUMERIC(4,1),
    CASE WHEN nivel_riesgo_urbano IN ('ND', '') THEN NULL
         WHEN nivel_riesgo_urbano = 'Riesgo alto' THEN 'Alto riesgo'
         WHEN nivel_riesgo_urbano = 'Riesgo bajo' THEN 'Bajo riesgo'
         ELSE nivel_riesgo_urbano END,
    NULLIF(NULLIF(irca_rural, 'ND'), '')::NUMERIC(4,1),
    CASE WHEN nivel_riesgo_rural IN ('ND', '') THEN NULL
         WHEN nivel_riesgo_rural = 'Riesgo alto' THEN 'Alto riesgo'
         WHEN nivel_riesgo_rural = 'Riesgo bajo' THEN 'Bajo riesgo'
         ELSE nivel_riesgo_rural END
FROM irca_raw;
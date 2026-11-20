-- Verificación de la carga y la limpieza (PostgreSQL / Neon)

-- 1. Los conteos deben coincidir con el CSV original (19160 filas)
SELECT
  (SELECT COUNT(*) FROM irca_raw) AS filas_raw,
  (SELECT COUNT(*) FROM irca)     AS filas_limpia;

-- 2. Deben quedar 5 niveles de riesgo (se unificaron 7 etiquetas)
SELECT nivel_riesgo, COUNT(*) AS filas
FROM irca
GROUP BY nivel_riesgo
ORDER BY filas DESC;
-- Esperado: Sin riesgo 5979, Riesgo medio 4658, Alto riesgo 4259,
--           Bajo riesgo 3905, Inviable sanitariamente 359

-- 3. Valores no disponibles (ND convertidos a nulo) y filas consolidadas por departamento
SELECT
  COUNT(*) FILTER (WHERE irca_urbano IS NULL)       AS urbano_nulos,   -- 1268
  COUNT(*) FILTER (WHERE irca_rural IS NULL)        AS rural_nulos,    -- 9615
  COUNT(*) FILTER (WHERE es_agregado_departamental) AS filas_todos     -- 569
FROM irca;

-- 4. Cobertura temporal y territorial
SELECT MIN(anio) AS desde, MAX(anio) AS hasta,
       COUNT(DISTINCT departamento_codigo) AS departamentos            -- 2007, 2024, 33
FROM irca;
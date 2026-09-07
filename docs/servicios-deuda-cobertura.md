# Servicios de deuda provinciales — revisión 6/9/2026

Se elimina la restricción que ocultaba el calendario fuera de Buenos Aires. Todas las jurisdicciones tienen la misma ficha, con faltantes explícitos y fuentes descargables.

## Historia común
DNAP: 24 jurisdicciones, 2005–2025 y primer trimestre 2026. Servicios **devengados**, preliminares y netos de deuda indirecta. No equivalen a pagos efectivos ni a un calendario futuro. Se mantienen los vacíos originales; cero solo cuando la fuente publica cero. CABA se convierte de miles a millones de pesos. No se deflacta una suma anual sin una distribución mensual verificada. Año completo y trimestre se identifican separadamente.

Cuatro diferencias entre las planillas provinciales 2025 y el consolidado (Jujuy, Mendoza, Misiones y Santa Fe) quedan registradas en JSON; se conserva la serie provincial. El importador guarda la huella SHA256 de las 24 planillas.

## Calendarios futuros
- Buenos Aires: 2026–2041, informe al 31/12/2025, millones de pesos.
- Córdoba: 2026–2032, presupuesto actualizado 2/1/2026, Administración Central + ACIF. Los PDF originales están en pesos: se dividen por un millón. La segunda serie incluye intereses **y gastos**.
- Otras 22 jurisdicciones: sin calendario futuro verificado cargado. No significa ausencia de deuda o de publicaciones oficiales.
- CABA: el enlace oficial al perfil de junio de 2026 devolvió 404 durante esta revisión.
- Entre Ríos: se encontró https://www.entrerios.gov.ar/presupuesto/leypres/p26-28/pdf/ANEXO1.pdf . No se incorporan importes hasta corroborar su unidad; el anexo extraído no la declara explícitamente.

Los calendarios representan lo previsto en cada publicación. No descuentan pagos posteriores ni incorporan nuevas operaciones: no deben presentarse como saldo pendiente a hoy. Sus fechas y alcances diferentes impiden tratarlos como una comparación homogénea de proyecciones.

## Reproducción
Ejecutar `scripts_build_provincial_debt_services.py` con el directorio de fuentes en caché. Los enlaces originales de cada observación se guardan en CSV y JSON. El caché contiene 24 planillas por provincia, `province-sources.json`, `services2025.xlsx`, `services2026.xlsx`, `cordoba-capital.pdf` y `cordoba-interest.pdf`.

"""Reproducible discussion targets; never official or approved commitments."""
import csv
import json
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parent
IDS = {'homicide_rate': ('Seguridad', 'cada 100.000 habitantes', -1),
       'language_high': ('Educación', '%', 1),
       'math_high': ('Educación', '%', 1),
       'infant_mortality': ('Salud', 'cada 1.000 nacidos vivos', -1)}

def build():
    source = json.loads((ROOT/'data/government_results_provinces.json').read_text(encoding='utf-8'))
    metrics = [(province, pillar, m) for province, data in source['provinces'].items()
               for pillar in data['pillars'] for m in pillar['metrics'] if m['id'] in IDS]
    medians = {key: median(m['value'] for _, _, m in metrics if m['id'] == key and m['rank'] is not None) for key in IDS}
    rows = []
    for province, pillar, m in metrics:
        area, unit, direction = IDS[m['id']]
        base, reference = m['value'], medians[m['id']]
        eligible = m['rank'] is not None
        behind = (reference-base)*direction > 0
        target = round(base+(reference-base)/2 if behind else base, 2) if eligible else None
        rows.append(dict(provincia=province, indicador=m['label'], id=m['id'], area=area,
                         valor_base=base, periodo_base=m['period'], unidad=unit,
                         referencia_mediana=reference, universo_referencia=sum(x['id']==m['id'] and x['rank'] is not None for _,_,x in metrics),
                         meta_propuesta=target, estado='Propuesta para discutir; no aprobada',
                         criterio=('Cerrar la mitad de la brecha con la mediana' if behind else 'Sostener el resultado de base') if eligible else 'Actualizar medición con cobertura suficiente antes de fijar una meta numérica',
                         horizonte='48 meses desde la asunción; actualizar la base al inicio' if eligible else 'Primeros 12 meses: acordar medición comparable',
                         responsable_funcional='Área provincial de '+area,
                         seguimiento='Anual; sujeto a publicación de la fuente', fuente=m['source_url'],
                         nota_cobertura=pillar.get('quality_note','')))
    document = dict(reviewed_at='2026-09-06', methodology='Ejercicio de planificación: cerrar en 48 meses la mitad de la brecha con la mediana de jurisdicciones elegibles del mismo indicador y período; sostener la base cuando ya iguala o supera esa referencia. El 50% es un supuesto de trabajo, no una estimación de factibilidad ni del efecto de una política. No es una meta oficial. Antes de adoptarla, actualizar la base y costear las acciones. No se fija objetivo numérico con cobertura educativa insuficiente.', rows=rows)
    (ROOT/'data/management_proposals.json').write_text(json.dumps(document,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/'data/management_proposals.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    return document

if __name__ == '__main__':
    print(len(build()['rows']), 'propuestas con base, criterio, plazo y área responsable')

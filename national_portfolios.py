"""Jurisdiction sheets: named source match, reconciled money, real PA IDs."""
import unicodedata


def fold(s):
    return ''.join(c for c in unicodedata.normalize('NFD',s.lower()) if not unicodedata.combining(c))


def build_portfolios(b, management, physical):
    result=[]
    for j in b['jurisdictions']:
        rows=[r for r in management['execution']['groups']['jurisdiccion'] if fold(r['jurisdiccion_desc'])==fold(j['name'])]
        assert len(rows)==1, j['name']
        observed=rows[0];code=observed['jurisdiccion_id']
        for old,new in [('law','credito_presupuestado'),('current','credito_vigente'),('accrued','credito_devengado')]:
            assert abs(j[old]-observed[new])<.01, (code,old)
        programs=sorted([p for p in b['programs'] if p['jurisdiction']==j['name']],key=lambda p:(-p['project'],p['id']))
        works=sorted([w for w in b['works'] if w['jurisdiction']==j['name']],key=lambda w:(-w['project'],w['id']))
        metas=[r for r in physical if r['jurisdiccion_id']==code]
        assert all(r['trimestre']==2 and r['ejercicio_presupuestario']==2026 and not r['requiere_revision_clave'] for r in metas)
        total=sum(p['project'] for p in programs)
        if j['project'] is not None:
            assert abs(total-j['project'])<=(len(programs)+1)*.5, (code,total,j['project'])
        else:
            assert not programs and not works
        result.append({'id':code,'name':j['name'],'project':j,'execution':observed,
            'program_ids':[p['id'] for p in programs], 'work_ids':[w['id'] for w in works],
            'capital':sum(p['capital'] for p in programs) if programs else None,
            'works_total':sum(w['project'] for w in works) if j['project'] is not None else None,
            'program_rounding_difference':total-j['project'] if j['project'] is not None else None,
            'physical':{'count':len(metas),'reported':sum(r['ejecutado_acumulado_trim2'] is not None for r in metas),
                        'comparable':sum(r['ejecutado_acumulado_trim2'] is not None and (r['programacion_acumulada_trim2'] or 0)>0 for r in metas)},
            'scope_note':j.get('note') or 'Comparación con la estructura de cada año. Los traslados de funciones pueden explicar parte del cambio.'})
    assert len({p['id'] for p in result})==len(result)==16
    assert sum(p['physical']['count'] for p in result)==len(physical)
    assert sorted(i for p in result for i in p['program_ids'])==sorted(p['id'] for p in b['programs'])
    assert sorted(i for p in result for i in p['work_ids'])==sorted(w['id'] for w in b['works'])
    return result

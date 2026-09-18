"""Editorial readings grounded in specific physical records; shared by web and PDF."""
def number(v):
    return f'{v:,.0f}'.replace(',', '.')


def readings(slug, rows):
    def pick(measure, unit=None, sub=None):
        found=[r for r in rows if r['medicion_fisica_id']==measure
               and (unit is None or r['unidad_medida_desc']==unit)
               and (sub is None or r['subprograma_id']==sub)]
        assert len(found)==1, (slug,measure,unit,sub)
        return found[0]
    selected=[]
    if slug=='jubilaciones':
        selected=[pick(71,sub=1),pick(71,sub=3),pick(72,sub=1),pick(72,sub=3)]
        a,b,c,d=selected
        reading=f"El primer semestre registra un promedio de {number(a['ejecutado_acumulado_trim2'])} jubilaciones del régimen de reparto y {number(b['ejecutado_acumulado_trim2'])} por moratoria. Las pensiones promedian {number(c['ejecutado_acumulado_trim2'])} y {number(d['ejecutado_acumulado_trim2'])}, respectivamente. Son promedios de prestaciones informadas, no altas nuevas ni personas distintas acumuladas en seis meses."
        recommendation='Para evaluar si el presupuesto alcanza, hay que separar cuántas prestaciones se pagan y cuánto compra cada haber. Una suba real del gasto total puede responder a cambios en la cantidad o composición de las prestaciones; no demuestra una mejora equivalente para cada jubilado.'
    elif slug=='alimentacion':
        selected=[pick(685),pick(686),pick(3410)]
        a,b,c=selected
        reading=f"En espacios comunitarios se informa un promedio de {number(a['ejecutado_acumulado_trim2'])} personas asistidas frente a {number(a['programacion_acumulada_trim2'])} previstas. La línea Alimentar Comunidad registra {number(b['ejecutado_acumulado_trim2'])} frente a {number(b['programacion_acumulada_trim2'])}; el organismo explica demoras en los convenios. Los {number(c['ejecutado_acumulado_trim2'])} módulos alimentarios son entregas acumuladas y no se suman a esos promedios."
        recommendation='Recomendamos revisar la renovación de convenios y el poder de compra de las ayudas. El archivo no informa una ejecución acumulada de la Prestación Alimentar: estas mediciones de espacios comunitarios no describen toda la cobertura del programa.'
    elif slug=='medicamentos':
        selected=[pick(1244,'Paciente Asistido'),pick(1244,'Unidad Distribuida'),pick(1617,'Botiquín Distribuido')]
        a,b,_=selected
        reading=f"La asistencia oncológica registra {number(a['ejecutado_acumulado_trim2'])} pacientes frente a {number(a['programacion_acumulada_trim2'])} previstos, y {number(b['ejecutado_acumulado_trim2'])} unidades de medicamentos frente a {number(b['programacion_acumulada_trim2'])}. El organismo atribuye los desvíos a plazos de compra más largos que los estimados. Pacientes y unidades distribuidas miden cosas distintas."
        recommendation='Recomendamos revisar licitaciones, existencias y fechas de entrega. Más crédito puede ampliar las compras, pero no resuelve por sí solo una demora administrativa. Este registro no permite determinar qué pacientes quedaron sin tratamiento ni durante cuánto tiempo.'
    elif slug=='seguridad-federal':
        selected=[pick(2599),pick(3485),pick(1822)]
        a,b,c=selected
        reading=f"La PFA informó un promedio de {number(a['ejecutado_acumulado_trim2'])} vehículos controlados por día frente a {number(a['programacion_acumulada_trim2'])} previstos. Explicó que destinó personal a otros operativos. Los procedimientos contra el narcotráfico fueron {number(b['ejecutado_acumulado_trim2'])} frente a {number(b['programacion_acumulada_trim2'])}; los mandatos judiciales cumplidos, {number(c['ejecutado_acumulado_trim2'])}."
        recommendation='Recomendamos contrastar el despliegue de personal con la carga de trabajo y las prioridades operativas. La cantidad de controles o procedimientos mide actividad policial; no equivale a una tasa de delitos ni demuestra, por sí sola, que haya más o menos seguridad.'
    else:
        return None
    keys=['subprograma_id','tipo_medicion_fisica','medicion_fisica_id','unidad_medida_id']
    return {'reading':reading,'recommendation':recommendation,
            'selection':[{k:r[k] for k in keys} for r in selected]}

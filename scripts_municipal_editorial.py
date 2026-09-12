"""Curated municipal reports: three core pages and independent optional topics."""
import io
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DictionaryObject, NameObject, NumberObject, ArrayObject, DecodedStreamObject
from reportlab.pdfbase import pdfmetrics
from scripts_export_municipal_reports import (Report, ROOT, SITE, CONTENT, WIDTH, HEIGHT, MARGIN,
    BaseDocTemplate, Frame, PageTemplate, Canvas, Table, TableStyle, Paragraph, Spacer,
    colors, PALE, TEAL, INK, finite, number, money, pct, ratio, date, escaped, source_link)

TOPICS = [
    ('lectura','Diagnóstico y decisiones','La situación del municipio y tres prioridades concretas.',True),
    ('cuentas','Cuentas, presupuesto y transferencias','Ingresos, gastos, autorización anual y fondos provinciales.',True),
    ('economia','Trabajo, salarios y actividad','Empleo formal, sectores, remuneraciones y producción local.',True),
    ('poblacion','Población, servicios y seguridad','Carencias, salud, vivienda y delitos registrados.',False),
    ('deudas','Deudas de las personas','Personas con crédito, atrasos y alcance del relevamiento.',False),
    ('detalle-fiscal','Detalle de ejecución presupuestaria','Partidas, pagos, origen de recursos y conciliaciones disponibles.',False),
    ('caja','Caja y deuda municipal','Saldos, obligaciones y límites de la información disponible.',False),
    ('historia','Historia de las cuentas','Resultados de distintos años con sus períodos exactos.',False),
    ('bancos','Crédito y depósitos bancarios','Saldos por localización financiera y fechas de cada serie.',False),
]

def latest_fiscal(m):
    return max((f for f in [m.get('fiscal'),m.get('fiscalOther')] if f),key=lambda f:f['fin'],default=None)

def document_refs(m, documents):
    return 'Municipalidad de '+escaped(m['municipio'])+' · '+' · '.join(
        source_link(d['url'],'documento '+str(i)) for i,d in enumerate(documents,1))

def direction(v, positive='creció', negative='cayó'):
    return positive if v>0 else negative if v<0 else 'no cambió'

class EditorialReport(Report):
    def __init__(self,path,m,data,geography,topic):
        super().__init__(path,m,data,geography)
        self.topic=topic;self.numbered=False
        self.styles['body'].fontSize=10.5;self.styles['body'].leading=15
        self.styles['h2'].spaceBefore=8;self.styles['h2'].spaceAfter=6
        self.styles['h1'].fontSize=24;self.styles['h1'].leading=29

    def core_overview(self):
        m=self.m;f=latest_fiscal(m);r=m['variacion_transferencias_real_pct'];j=m['empleo_promedio_cambio_2024_2025_pct']
        self.section(escaped(m['municipio']),False,self.refs('population','transfers','ipc','oede')+(' · '+self.fiscal_refs(f) if f else ''))
        self.p('LECTURA PARA LA GESTIÓN MUNICIPAL','small')
        self.p(f"{number(m['poblacion_2022'],0)} habitantes · Censo 2022. Datos incorporados al {date(self.data['generated'])}. Cada indicador conserva su período.",'small')
        kpis=[('Transferencias reales',pct(r),'Ene-jul 2026 vs. 2025'),('Empleo privado formal',pct(j),'Promedio 2025 vs. 2024'),('Resultado fiscal',money(f['resultado_financiero'])+' M' if f else 'Sin dato',date(f['fin']) if f else 'Cuenta pendiente')]
        cells=[]
        for label,value,period in kpis:
            color='#b42318' if value.startswith('-') else '#203331'
            cells.append([Paragraph(escaped(label),self.styles['kpilabel']),Paragraph(f'<font color="{color}">{escaped(value)}</font>',self.styles['kpi']),Paragraph(escaped(period),self.styles['kpilabel'])])
        t=Table([cells],colWidths=[CONTENT/3]*3)
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)]))
        self.story.extend([t,Spacer(1,12)])
        self.h('La lectura central')
        resource='Los fondos provinciales perdieron poder de compra. Esto puede presionar sobre los servicios y las obras que se financian con esos recursos.' if r<0 else 'Los fondos provinciales ganaron poder de compra. La mejora amplía los recursos de ese origen, aunque el margen final depende también de los gastos.' if r>0 else 'Los fondos provinciales mantuvieron su poder de compra. El margen para sostener servicios depende de los demás ingresos y de los costos.'
        employment='El empleo formal también retrocedió en su último año disponible.' if j<0 and r<0 else 'El empleo formal retrocedió en su último año disponible.' if j<0 else 'El empleo formal creció en su último año disponible.' if j>0 else 'El empleo formal se mantuvo estable en su último año disponible.'
        self.p(f'{resource} {employment} Son dos señales para la gestión, con cortes distintos: las transferencias llegan a julio de 2026 y el empleo, a diciembre de 2025. No permiten afirmar cómo está evolucionando el trabajo durante 2026.')
        if f:
            balance=f['resultado_financiero'];status='déficit' if balance<0 else 'superávit' if balance>0 else 'equilibrio'
            self.p(f"Las cuentas muestran <b>{status}</b> al {date(f['fin'])}. Por cada $100 de ingresos se registraron ${number(ratio(f['gastos_totales'],f['ingresos_totales']),1)} de gastos. "+('El faltante exige identificar cómo se financió.' if balance<0 else 'Ese resultado no equivale a caja libre: puede haber obligaciones pendientes y fondos con destino asignado.'))
        else:self.p('<b>La cuenta fiscal está pendiente.</b> Las transferencias son sólo una parte de los ingresos. Sin ingresos y gastos del mismo período no se puede afirmar que hay déficit o superávit.')
        self.h('Tres decisiones que conviene ordenar')
        self.p('<b>1. Revisar recursos y compromisos.</b> '+('La pérdida de poder de compra obliga a actualizar el costo de los servicios y contrastarlo con tasas propias y giros provinciales. Así se identifica qué compra u obra necesita reprogramarse.' if r<0 else 'Antes de asumir gastos permanentes, conviene contrastar los ingresos efectivamente cobrados con los costos de los servicios y el destino obligatorio de cada fondo.'))
        self.p('<b>2. Armar el calendario de pagos.</b> Reunir saldos bancarios, fondos afectados, facturas pendientes y vencimientos. Esto permite saber qué compromisos se pueden atender y cuándo; el resultado fiscal por sí solo no responde esa pregunta.')
        largest=max((s for s in m['sectors'] if finite(s['jobs'])),key=lambda s:s['jobs'],default=None)
        concentration=(f"El sector «{escaped(largest['name'])}» concentra el {number(ratio(largest['jobs'],m['empleo_dic2025']),1)}% de los puestos registrados. " if largest and m['empleo_dic2025']>0 else '')
        self.p('<b>3. Mirar los sectores que explican el empleo.</b> '+concentration+('La caída de puestos puede afectar los ingresos de las familias vinculadas a esas empresas y el comercio.' if j<0 else 'El crecimiento puede concentrarse en pocas actividades; el total no muestra quiénes participan de la mejora.' if j>0 else 'Un total estable puede esconder cambios entre actividades.')+' Contrastar los sectores con habilitaciones y cobranza ayuda a priorizar trámites, capacitación o infraestructura con una necesidad identificada.')
        self.p('Real significa ajustado por inflación. M significa millones de pesos. El empleo se ubica por establecimiento; no mide desocupación ni sólo trabajadores residentes.','small')

    def core_accounts(self):
        m=self.m;f=latest_fiscal(m);b=m.get('annualBudget')
        refs=self.refs('transfers','ipc')+(' · '+self.fiscal_refs(f) if f else '')
        if b:refs+=' · '+document_refs(m,b['documents'])
        self.section('Cuentas y recursos',False,refs)
        self.p('Tres datos distintos: el presupuesto autoriza gasto anual, la cuenta fiscal registra ingresos y gastos de un período, y las transferencias son fondos que llegan de la Provincia. No se suman entre sí.','small')
        self.h('Cuánto tiene autorizado gastar')
        if b:
            kind='vigente' if b['basis']=='current' else 'original'
            self.p(f"Presupuesto <b>{kind} de {b['year']}: {money(b['amount'])} millones</b>. Corte o documento: {date(b['asOf'])}. Equivale a {money(b['perCapita'],0,False)} por habitante del Censo 2022.")
            if b['historical']:self.p(f"Es un dato histórico: falta verificar el presupuesto de 2026.",'small')
            elif b['basis']=='original':self.p('Es el monto inicial; todavía no incorporamos una actualización del vigente.','small')
            self.p('Es autorización anual, no gasto ejecutado ni saldo en el banco. '+escaped(b['scope']),'small')
        else:self.p('Presupuesto anual pendiente de verificación. No se estima a partir de transferencias ni de gastos parciales.')
        self.h('Qué muestran las cuentas')
        if f:
            self.p(f"Del {date(f['inicio'])} al {date(f['fin'])}. Millones de pesos corrientes, sin ajuste por inflación.",'small')
            self.table(['Concepto','Ingresos cobrados','Gastos registrados'],[
                ('Funcionamiento corriente',money(f['ingresos_corrientes'],2),money(f['gastos_corrientes'],2)),
                ('Capital: obras, bienes y transferencias',money(f['ingresos_capital'],2),money(f['gastos_capital'],2)),
                ('Total, sin operaciones financieras',money(f['ingresos_totales'],2),money(f['gastos_totales'],2)),
            ],[CONTENT*.48,CONTENT*.26,CONTENT*.26],True)
            self.p(f"<b>Resultado financiero: {money(f['resultado_financiero'],2)} millones</b>, equivalente al {pct(f['resultado_sobre_ingresos_pct'],1)} de los ingresos. El gasto de capital representa {pct(f['capital_sobre_gasto_pct'],1)} del gasto total.")
            if finite(f.get('personal_devengado')):self.p(f"Personal: {money(f['personal_devengado'],2)} millones, el {pct(f.get('personal_sobre_gasto_corriente_pct'),1)} del gasto corriente.",'small')
            self.p('Los gastos son devengados: obligaciones registradas, aunque no estén pagadas. El resultado no es caja libre. '+escaped(f.get('scope','Cuenta municipal publicada.')),'small')
            if f is m.get('fiscalOther'):self.p('Este cierre no integra el ranking fiscal de enero-junio de 2026.','small')
        else:self.p('Faltan ingresos y gastos comparables. '+('La ejecución disponible incluye operaciones financieras que todavía requieren conciliación.' if m.get('fiscalExecution') else 'No corresponde calcular un resultado con las transferencias provinciales solamente.'))
        self.h('Qué llega de la Provincia')
        self.table(['Enero-julio de cada año','2025','2026'],[
            ('Transferencias: millones de pesos corrientes',money(m['transferencias_2025_ene_jul_ars']),money(m['transferencias_2026_ene_jul_ars'])),
            ('Transferencias: millones de pesos de julio 2026',money(m['transferencias_2025_ene_jul_ars_jul26']),money(m['transferencias_2026_ene_jul_ars_jul26'])),
            ('De ellas, coparticipación: millones de pesos de julio 2026',money(m['copart_2025_ene_jul_ars_jul26']),money(m['copart_2026_ene_jul_ars_jul26'])),
        ],[CONTENT*.52,CONTENT*.24,CONTENT*.24],True)
        self.p('La coparticipación ya está incluida en las transferencias: no se suma otra vez. Para comparar poder de compra se ajusta cada mes con el IPC nacional antes de sumar. Una baja de un impuesto provincial no se traslada automáticamente en igual porcentaje a estos fondos.','small')

    def core_economy(self):
        m=self.m;w=m['community']['wage']['annual'];j=m['empleo_promedio_cambio_2024_2025_pct'];d=m['empleos_cambio_dic2023_dic2025']
        self.section('Trabajo y economía local',False,self.refs('oede','ipc','pbg')+' · '+source_link('https://www.argentina.gob.ar/sites/default/files/departamento_series_empleo_y_salarios_mensual_sector_1.csv','OEDE, sectores de actividad'))
        self.h('Cómo se movieron los puestos y los salarios')
        self.p('Salarios en pesos de julio de 2026, ajustados mes a mes por inflación.','small')
        self.table(['Año','Puestos promedio','Puestos en diciembre','Salario bruto mensual real'],[
            (str(y),number(m[f'empleo_promedio_{y}'],1),number(m[f'empleo_dic{y}'],0),money(w[str(y)]['real'],0,False)) for y in [2023,2024,2025]
        ],[CONTENT*.12,CONTENT*.25,CONTENT*.27,CONTENT*.36],True)
        self.p(f"El promedio de empleo {direction(j)} {number(abs(j),1)}% en 2025 frente a 2024. Entre diciembre de 2023 y diciembre de 2025 hubo {number(abs(d),0)} puestos {'menos' if d<0 else 'más' if d>0 else 'de diferencia'}. El promedio y el cierre pueden moverse en distinta dirección; comparan momentos diferentes.")
        self.p('Se cuentan puestos privados registrados por lugar del establecimiento. Quedan fuera el empleo público, informal e independiente. Algunos trabajadores viven en otro municipio: esta serie no mide la desocupación de los vecinos.','small')
        self.p(f"El salario bruto mensual promedio de 2025 fue de <b>{money(w['2025']['nominal'],0,False)}</b> en pesos de ese año. La tabla lo lleva a precios de julio de 2026. Incluye aguinaldo y otros pagos: <b>no es el sueldo de bolsillo ni el salario de un vecino típico.</b>")
        self.p('El OEDE usa las remuneraciones declaradas al SIPA. Para el promedio real se ajusta cada salario mensual por IPC de julio de 2026 / IPC del mes y luego se promedian los doce meses. El peso de cada sector y los sueldos altos pueden mover el promedio.','small')
        self.h('Dónde están los puestos')
        names={'Explotacion de minas y canteras':'Minería','Electircidad, gas y agua':'Electricidad, gas y agua','Construccion':'Construcción','Agricultura, ganaderia y pesca':'Agro y pesca'}
        sectors=sorted(m['sectors'],key=lambda s:s['jobs'] if finite(s['jobs']) else -1,reverse=True)
        self.table(['Sector · diciembre de 2025','Puestos','Parte del total'],[(names.get(s['name'],s['name']),number(s['jobs'],0),pct(ratio(s['jobs'],m['empleo_dic2025']),1)) for s in sectors],[CONTENT*.60,CONTENT*.20,CONTENT*.20],True)
        self.p('Los sectores reservados quedan sin dato; no se completan con cero ni se estima su parte del total.','small')
        self.h('Qué produce el territorio')
        self.p(f"El producto bruto municipal de 2023 fue de {money(m['pbg_constante_2004_2023_ars'],2)} millones a precios constantes de 2004. Frente a 2021, {direction(m['pbg_real_cambio_2021_2023_pct'])} {number(abs(m['pbg_real_cambio_2021_2023_pct']),1)}%, sin el efecto de la inflación. Es una estimación de la DPE de los bienes y servicios producidos, no recaudación ni presupuesto. El último año disponible es 2023.",'small')

    def debt_brief(self):
        d=self.m['community']['debt'];self.section('Deudas de las personas',False,self.refs('credit'))
        self.p('Julio de 2026 · Relevamiento CEC/FES sobre registros del BCRA.','small')
        self.p('El dato ayuda a reconocer presión sobre las finanzas de las personas con deuda registrada. No describe a toda la población ni a las finanzas del gobierno municipal.')
        self.table(['Indicador','Dato'],[
            ('Personas con deuda registrada',number(d['peopleWithDebt'],0)),('Personas en mora',number(d['peopleInArrears'],0)),
            ('Personas en mora / personas con deuda',pct(d['peopleInArrearsPct'],2)),
            ('Deuda total, millones de pesos corrientes',money(d['debtARS'],2)),('Deuda en mora, millones de pesos corrientes',money(d['debtInArrearsARS'],2)),
            ('Deuda en mora / deuda total',pct(d['debtInArrearsPct'],2)),('Deuda promedio por persona con deuda, pesos',money(d['averageDebtARS'],0,False))
        ],[CONTENT*.7,CONTENT*.3])
        self.h('Cómo leerlo')
        self.p('Tener deuda no significa estar atrasado. La mora cuenta aquí las situaciones 3, 4 y 5 del relevamiento; los atrasos más cortos quedan fuera. El porcentaje de personas en mora cuenta personas. El porcentaje de deuda en mora cuenta dinero: pueden diferir porque no todos deben el mismo monto.')
        self.p('Ninguno de esos porcentajes se calcula sobre todos los habitantes ni cuenta hogares. Una familia puede tener varios deudores. El promedio tampoco indica cuánto debe un vecino típico.')
        self.h('Qué aporta a la gestión')
        self.p('Conviene contrastar esta señal con empleo, ingresos y consultas de defensa del consumidor. Puede orientar la atención de reclamos y la información sobre crédito. Un solo corte no permite atribuir la mora a una causa ni estimar cuánto caerá el consumo local.')
        self.p('El CEC/FES procesa y asigna los datos al territorio; no es una serie municipal publicada directamente por el BCRA. Se toman todas las entidades, edades y géneros del relevamiento. No se verificaron domicilios individuales. No cubre toda la deuda informal ni solamente crédito para consumo.','small')

    def detail_accounts(self):
        m=self.m;g=m.get('management');e=m.get('fiscalExecution')
        if g:
            b=g['budget'];self.section('Detalle de presupuesto y pagos',False,document_refs(m,b['documents']))
            self.p(f"Del {date(b['inicio'])} al {date(b['fin'])}. Millones de pesos corrientes. Vigente es la autorización anual; devengado, la obligación registrada; pagado, lo cancelado.",'small')
            self.p('Autorización anual: '+'. '.join(label+': '+money(b[key],2) for key,label in [('original','Original'),('modifications','Modificaciones'),('current','Vigente')] if finite(b.get(key)))+'. Millones de pesos.','small')
            self.table(['Concepto','Millones de pesos'],[(label,money(b.get(key),2)) for key,label in [('received','Recursos cobrados'),('accrued','Gasto devengado'),('paid','Gasto pagado'),('unpaid','Devengado del período sin pagar')] if finite(b.get(key))],[CONTENT*.67,CONTENT*.33],True)
            self.table(['Objeto del gasto','Vigente','Devengado','Pagado'],[(r['label'],money(r['current'],2),money(r['accrued'],2),money(r['paid'],2)) for r in b['objects']],[CONTENT*.4,CONTENT*.2,CONTENT*.2,CONTENT*.2],True)
            self.h(b['receiptTitle'])
            self.table(['Concepto','Cobrado','Parte del total'],[(r['label'],money(r['received'],2),pct(ratio(r['received'],b['received']),1)) for r in b['receipts']],[CONTENT*.52,CONTENT*.28,CONTENT*.2],True)
            self.p('El devengado sin pagar es del período, no toda la deuda. Los totales incluyen operaciones financieras. Bienes de uso no agota el capital: también hay insumos de obras y transferencias.','small')
            bridge=b.get('reconciliation')
            if bridge:
                self.h('Cómo se llega al gasto fiscal')
                self.table(['Conciliación','Millones de pesos'],[(label,money(value,2)) for label,value in [('Gasto presupuestario devengado',bridge['budgetAccrued']),('Menos devolución de capital de préstamos',-bridge['amortization']),('Menos cancelación de pasivos anteriores',-bridge['priorLiabilities']),('Gasto fiscal del período',bridge['fiscalExpenditure']),('Intereses, ya incluidos',bridge['interestIncluded'])]],[CONTENT*.7,CONTENT*.3],True)
                self.p('Pagar obligaciones de años anteriores consume caja, pero no constituye nuevo gasto fiscal de este período. El capital de los préstamos también se separa; los intereses permanecen en el gasto.','small')
        elif e:
            self.section('Detalle de ejecución presupuestaria',False,self.fiscal_refs(e))
            self.p(f"Del {date(e['inicio'])} al {date(e['fin'])}. Millones de pesos corrientes. Los totales incluyen operaciones financieras: no se restan sin conciliación para calcular déficit.")
            self.table(['Concepto','Millones de pesos'],[(label,money(e.get(key),2)) for key,label in [('presupuesto_vigente','Autorización anual vigente'),('recursos_presupuestarios_percibidos','Recursos cobrados'),('gastos_presupuestarios_devengados','Gastos devengados'),('gastos_presupuestarios_pagados','Gastos pagados'),('devengado_no_pagado_del_periodo','Gastos del período sin pagar')]])
            self.p('Devengado significa obligación registrada, aunque no se haya pagado. Lo devengado y no pagado del período no representa toda la deuda ni demuestra que esas facturas estén vencidas.')

    def cash(self):
        g=self.m['management'];t=g['treasury'];d=g.get('debt')
        self.section('Caja y deuda municipal',False,document_refs(self.m,t['documents'])+' · '+source_link(SITE+'auditoria-distritos.html#'+self.m['id'],'criterios y documentos complementarios'))
        self.p('Son saldos a una fecha, no gastos del semestre. Los subtotales ya están incluidos en sus totales; no se suman nuevamente.','small')
        self.h('Tesorería y pasivos al '+date(t['date']))
        labels={'closing':'Saldo de tesorería','available':'Disponibilidades, incluidas arriba','transitory':'Movimientos transitorios, incluidos arriba','budgetCash':'Cuentas presupuestarias','unearmarkedAccounts':'De ellas: sin afectación','earmarkedAccounts':'De ellas: con destino asignado','thirdPartyAndSpecial':'Terceros y cuentas especiales','liabilities':'Pasivos contables','currentLiabilities':'De ellos: corrientes','nonCurrentLiabilities':'De ellos: no corrientes'}
        self.table(['Concepto','Millones de pesos corrientes'],[(label,money(t[key],2)) for key,label in labels.items() if finite(t.get(key))],[CONTENT*.67,CONTENT*.33],True)
        self.p(escaped(t['reading']),'small')
        if d:
            self.h('Deuda al '+date(d['date']))
            self.table(['Concepto','Millones de pesos corrientes'],[(label,money(d.get(key),2)) for key,label in [('consolidated','Deuda consolidada'),('current','De ella: corriente'),('nonCurrent','De ella: no corriente'),('floating','Deuda flotante')]],small=True)
            self.p(escaped(d['reading']),'small')
        self.p('Los pasivos registran obligaciones; corriente identifica corto plazo, no necesariamente una factura vencida. La caja disponible exige conocer afectaciones y vencimientos. Estos saldos no prueban por sí solos cuánto se puede comprometer.')
        self.h('Qué falta para completar esta lectura')
        for note in g['pending'][:3]:self.p('• '+escaped(note),'small')
        self.p(source_link(SITE+'auditoria-distritos.html#'+self.m['id'],'Consultar el detalle de los faltantes y sus documentos'),'small')

    def history(self):
        g=self.m['management'];portal='https://gobiernodelasheras.com/category/documentos/' if self.m['id']=='06329' else 'https://www.tigre.gob.ar/gobierno/informacion_gestion'
        self.section('Historia de las cuentas',False,source_link(portal,'Publicaciones oficiales del municipio')+' · '+source_link(SITE+'auditoria-distritos.html#'+self.m['id'],'documentos, períodos y conciliaciones'))
        self.p(escaped(g['historyReading']))
        for end,label in [(6,'Primer semestre'),(12,'Cierres anuales')]:
            records=[f for f in g['history'] if f['inicio'][5:7]=='01' and int(f['fin'][5:7])==end]
            if not records:continue
            self.h(label)
            self.table(['Período exacto','Ingresos','Gastos','Resultado','% ingresos'],[(date(f['inicio'])+' a '+date(f['fin']),money(f['ingresos_totales']),money(f['gastos_totales']),money(f['resultado_financiero']),pct(f['resultado_sobre_ingresos_pct'],1)) for f in records],[CONTENT*.3,CONTENT*.18,CONTENT*.18,CONTENT*.18,CONTENT*.16],True)
        self.p('Millones de pesos corrientes. Un monto mayor puede reflejar inflación; no se presenta como crecimiento real. Se comparan semestres con semestres y años con años. No se suman períodos que se superponen ni se proyecta automáticamente el resultado de junio al cierre anual.','small')
        self.p('La proporción del resultado sobre ingresos ayuda a dimensionar cada cierre, aunque no mide calidad de los servicios ni caja libre. El detalle contable de cada período permanece en la web.')

    def banking(self):
        m=self.m;bank=m.get('management',{}).get('banking');updated=bank and any(r['status']=='verified' for r in bank['records'])
        refs=self.refs('banks','ipc')
        if updated:refs+=' · '+document_refs(m,bank.get('documents',[]))
        self.section('Crédito y depósitos bancarios',False,refs)
        self.p('Los saldos se asignan por localización financiera. Pueden incluir operaciones de personas y empresas de otros lugares; no son la deuda de los vecinos ni depósitos del gobierno municipal.')
        if updated:
            self.p(escaped(bank['note']),'small')
            self.table(['Fecha','Préstamos corrientes','Depósitos corrientes','Préstamos reales','Depósitos reales'],[(date(r['date']),money(r.get('loans')),money(r.get('deposits')),money(r.get('loansReal')),money(r.get('depositsReal'))) for r in bank['records']],[CONTENT*.16,CONTENT*.21,CONTENT*.21,CONTENT*.21,CONTENT*.21],True)
        else:
            self.table(['Saldos al cierre','2023','2024'],[(label,money(m.get(f'{key}_2023_ars')),money(m.get(f'{key}_2024_ars'))) for key,label in [('prestamos','Préstamos, pesos corrientes'),('depositos','Depósitos, pesos corrientes')]],small=True)
        self.p('Los importes están en millones de pesos. Cuando se indica real, se ajustan con el IPC del mes de cierre a precios de julio de 2026. La moneda extranjera ya está convertida a pesos en la publicación; el tipo de cambio también puede afectar el saldo.','small')
        self.p(f"En 2024 había {number(m['sucursales_2024'],0)} sucursales informadas. La relación entre préstamos y depósitos de ese corte era {pct(m.get('prestamos_sobre_depositos_2024_pct'),1)}. Ese cociente no permite seguir el destino de cada depósito ni afirmar que el ahorro local se presta fuera del municipio.")
        self.p('Los rankings bancarios conservan 2024 como corte común entre municipios. Los datos más nuevos de una ficha no se usan para compararla contra cifras viejas de otra. Los importes faltantes permanecen como tales.','small')

    def render_module(self):
        methods={'lectura':self.core_overview,'cuentas':self.core_accounts,'economia':self.core_economy,'poblacion':self.community,'deudas':self.debt_brief,'detalle-fiscal':self.detail_accounts,'caja':self.cash,'historia':self.history,'bancos':self.banking}
        methods[self.topic]()
        doc=BaseDocTemplate(self.path,pagesize=(WIDTH,HEIGHT),title=f'{self.m["municipio"]} - Informe municipal',author='Federico Pellegrini',pageCompression=1)
        frame=Frame(MARGIN,104,CONTENT,HEIGHT-45-104,id='body',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
        doc.addPageTemplates(PageTemplate(id='municipal',frames=frame,onPageEnd=self.footer))
        def canvas(*args,**kwargs):kwargs['invariant']=1;return Canvas(*args,**kwargs)
        doc.build(self.story,canvasmaker=canvas)
        if self.topic in ['lectura','cuentas','economia'] and self.pages!=1:raise ValueError(f'La página breve {self.topic} desborda en {self.m["id"]}: {self.pages}')
        return self.pages

def add_page_number(page,writer,index):
    """A separate form keeps numbering removable when users select PDF topics."""
    label=f'Página {index}';x=WIDTH-MARGIN-pdfmetrics.stringWidth(label,'Helvetica',8)
    form=DecodedStreamObject();form.set_data(f'0.345 0.412 0.388 rg BT /FPNFont 8 Tf 1 0 0 1 {x:.3f} 14 Tm ('.encode()+label.encode('cp1252')+b') Tj ET')
    font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica'),NameObject('/Encoding'):NameObject('/WinAnsiEncoding')})
    form.update({NameObject('/Type'):NameObject('/XObject'),NameObject('/Subtype'):NameObject('/Form'),NameObject('/BBox'):ArrayObject([NumberObject(0),NumberObject(0),NumberObject(int(WIDTH)),NumberObject(int(HEIGHT))]),NameObject('/Resources'):DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/FPNFont'):writer._add_object(font)})})})
    resources=DictionaryObject(page['/Resources']);xobjects=DictionaryObject(resources.get('/XObject',DictionaryObject()).get_object())
    xobjects[NameObject('/FPPageNumber')]=writer._add_object(form);resources[NameObject('/XObject')]=xobjects;page[NameObject('/Resources')]=resources
    extra=DecodedStreamObject();extra.set_data(b'q /FPPageNumber Do Q')
    previous=page.raw_get('/Contents');values=list(previous.get_object()) if isinstance(previous.get_object(),ArrayObject) else [previous]
    page[NameObject('/Contents')]=ArrayObject(values+[writer._add_object(extra)])

def write_pdf(writer,path,m):
    writer.add_metadata({'/Title':m['municipio']+' - Informe municipal','/Author':'Federico Pellegrini'})
    with path.open('wb') as stream:writer.write(stream)

def build_editorial(path,brief_path,m,data,geography):
    writer=PdfWriter();modules=[];g=m.get('management');count=0
    for key,label,description,default in TOPICS:
        available=not(key in ['caja','historia'] and not g or key=='detalle-fiscal' and not(g or m.get('fiscalExecution')) or key=='bancos' and not(finite(m.get('prestamos_2024_ars')) or (g and any(r['status']=='verified' for r in g['banking']['records']))))
        if not available:continue
        buffer=io.BytesIO();report=EditorialReport(buffer,m,data,geography,key);pages=report.render_module();buffer.seek(0)
        pdf=PdfReader(buffer)
        for page in pdf.pages:
            writer.add_page(page);count+=1;add_page_number(writer.pages[-1],writer,count)
        modules.append({'id':key,'label':label,'description':description,'default':default,'required':key=='lectura','pages':list(range(count-pages,count))})
    write_pdf(writer,path,m)
    brief=PdfWriter();reader=PdfReader(path)
    for i in range(3):brief.add_page(reader.pages[i])
    write_pdf(brief,brief_path,m)
    return count,modules

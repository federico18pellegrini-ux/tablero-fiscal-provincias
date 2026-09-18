"""Editorial national reports, generated from the same frozen data as the dashboard.

python scripts_export_national_reports.py [--output DIR] [--check]
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.graphics.shapes import Drawing, Rect, String, Line, PolyLine
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Flowable, KeepTogether
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'nacion/reports'
SITE = 'https://tablero.federicopellegrini.com.ar/nacion/'
BASES = {'current': 'Vigente 2026', 'law': 'Inicial 2026', 'closing': 'Cierre estimado 2026'}
INPUTS = ['nacion/data/budget.json', 'data/ipc_source.json', 'scripts_export_national_reports.py', 'national_management_report.py', 'nacion/data/gestion.json',
          'national_decision_report.py', 'national_territory_report.py', 'nacion/data/decisions.json',
          'municipios/assets/manrope-400.ttf', 'municipios/assets/manrope-700.ttf']
INK, TEAL, MUTED, LINE, PALE, RED = map(colors.HexColor, ['#0a192f', '#254b73', '#64748b', '#e2e8f0', '#f1f5f9', '#b91c1c'])
PAGE_W, PAGE_H = A4
WIDTH = PAGE_W - 84
MONTHS = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre']

def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)

def num(value, digits=1):
    if not finite(value):
        return 's/d'
    return f'{value:,.{digits}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

def pct(value, signed=False):
    return (('+' if signed and value > 0 else '') + num(value) + '%') if finite(value) else 's/c'

def ratio(a, b):
    return 100 * a / b if finite(a) and finite(b) and b > 0 else None

def change(a, b):
    result = ratio(a, b)
    return result - 100 if result is not None else None

def money(value):
    if not finite(value):
        return 'sin dato'
    scale, label = (1e6, 'billones') if abs(value) >= 1e6 else (1e3, 'mil millones') if abs(value) >= 1e3 else (1, 'millones')
    return '$' + num(value / scale) + ' ' + label

def date(value):
    return '/'.join(reversed(value.split('-')))

def register_fonts():
    for name, path in [('Manrope', 'manrope-400.ttf'), ('ManropeBold', 'manrope-700.ttf')]:
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, str(ROOT / 'municipios/assets' / path)))
    pdfmetrics.registerFontFamily('Manrope', normal='Manrope', bold='ManropeBold', italic='Manrope', boldItalic='ManropeBold')

def styles():
    return {
        'body': ParagraphStyle('Body', fontName='Manrope', fontSize=10.2, leading=15.4, textColor=INK, spaceAfter=9),
        'lead': ParagraphStyle('Lead', fontName='Manrope', fontSize=12, leading=18.2, textColor=INK, spaceAfter=14),
        'title': ParagraphStyle('Title', fontName='ManropeBold', fontSize=26, leading=31, textColor=INK, spaceAfter=15),
        'heading': ParagraphStyle('Heading', fontName='ManropeBold', fontSize=13, leading=18, textColor=INK, spaceBefore=9, spaceAfter=7),
        'eyebrow': ParagraphStyle('Eyebrow', fontName='ManropeBold', fontSize=9, leading=13, textColor=TEAL, spaceAfter=7),
        'small': ParagraphStyle('Small', fontName='Manrope', fontSize=8, leading=11, textColor=MUTED, spaceAfter=6),
        'cell': ParagraphStyle('Cell', fontName='Manrope', fontSize=8.1, leading=10.6, textColor=INK),
        'num': ParagraphStyle('Number', fontName='Manrope', fontSize=8.1, leading=10.6, textColor=INK, alignment=2),
        'th': ParagraphStyle('TH', fontName='ManropeBold', fontSize=8, leading=10.5, textColor=INK),
    }

class SourceMarker(Flowable):
    def __init__(self, text):
        super().__init__()
        self.text = text
        self.width = self.height = 0

    def draw(self):
        self.canv._report_source = self.text

class Report:
    def __init__(self, data, mode='nominal', base='current'):
        self.d, self.mode, self.base = data, mode, base
        self.s = styles()
        self.story = []
        self.units = 'Pesos de agosto de 2026' if mode == 'real' else 'Pesos corrientes'
        self.base_label = BASES[base] + (f" al {date(data['meta']['execution_cutoff'])}" if base == 'current' else '')
        self.base_prose = {'current': f"lo autorizado para 2026 al {date(data['meta']['execution_cutoff'])}",
                           'law': 'lo aprobado al inicio de 2026',
                           'closing': 'la estimación de cierre de 2026'}[base]

    def value(self, value, year=2027):
        if not finite(value):
            return None
        return value * self.d['deflator']['annual_factors'][str(year)] if self.mode == 'real' else value

    def variation(self, row, real=None):
        if real is None:
            return change(self.value(row.get('project')), self.value(row.get(self.base), 2026))
        f = self.d['deflator']['annual_factors']
        return change(row.get('project') * f['2027'] if finite(row.get('project')) else None,
                      row.get(self.base) * f['2026'] if finite(row.get(self.base)) else None) if real else change(row.get('project'), row.get(self.base))

    def p(self, text, kind='body'):
        return Paragraph(text, self.s[kind])

    def add(self, text, kind='body'):
        self.story.append(self.p(text, kind))

    def section(self, label, title, source, first=False):
        if not first:
            self.story.append(PageBreak())
        self.story.append(SourceMarker(source))
        self.add(label.upper(), 'eyebrow')
        self.add(title, 'title')

    def note(self, text):
        self.add(text, 'small')

    def table(self, headings, rows, widths, compact=False):
        def cell(value, index, header=False):
            text = escape(str(value))
            if not header and index > 0 and str(value).startswith('-'):
                text = f'<font color="#b63836">{text}</font>'
            return self.p(text, 'th' if header else 'cell' if index == 0 else 'num')
        content = [[cell(v, i, True) for i, v in enumerate(headings)]] + [[cell(v, i) for i, v in enumerate(row)] for row in rows]
        t = Table(content, colWidths=widths, repeatRows=1, hAlign='LEFT')
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('BACKGROUND', (0, 0), (-1, 0), PALE),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8faf8')]),
            ('LINEBELOW', (0, 0), (-1, 0), .6, LINE), ('LINEBELOW', (0, -1), (-1, -1), .4, LINE),
            ('LEFTPADDING', (0, 0), (-1, -1), 6), ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 3 if compact else 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 3 if compact else 5),
        ]))
        self.story.extend([t, Spacer(1, 10)])

    def bars(self, rows, total, height=22):
        drawing = Drawing(WIDTH, len(rows) * height + 4)
        max_value = max((v for _, v in rows if finite(v)), default=1) or 1
        for index, (name, value) in enumerate(rows):
            y = (len(rows) - index - 1) * height + 6
            drawing.add(String(0, y + 2, name, fontName='Manrope', fontSize=8.2, fillColor=INK))
            drawing.add(Rect(204, y, 191, 10, fillColor=PALE, strokeColor=None))
            if finite(value):
                drawing.add(Rect(204, y, max(0, value / max_value * 191), 10, fillColor=TEAL, strokeColor=None))
            drawing.add(String(WIDTH, y + 1, num(ratio(value, total)) + '%', fontName='ManropeBold', fontSize=9, fillColor=INK, textAnchor='end'))
        self.story.extend([drawing, Spacer(1, 9)])

    def callout(self, title, text):
        box = Table([[self.p(title, 'heading')], [self.p(text)]], colWidths=[WIDTH])
        box.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), PALE), ('BOX', (0, 0), (-1, -1), .5, LINE),
                                ('LEFTPADDING', (0, 0), (-1, -1), 14), ('RIGHTPADDING', (0, 0), (-1, -1), 14)]))
        self.story.extend([KeepTogether(box), Spacer(1, 10)])

    def key_figures(self, total, nominal, real):
        metric = ParagraphStyle('Metric', parent=self.s['body'], fontName='ManropeBold', fontSize=21, leading=29, spaceAfter=2)
        values = [money(self.value(total)), pct(nominal, True), pct(real, True)]
        cells = []
        for label, value in zip(['Gasto propuesto 2027', 'Cambio en pesos', 'Cambio real'], values):
            text = f'<font color="#b63836">{value}</font>' if value.startswith('-') else value
            cells.append([self.p(label, 'small'), Paragraph(text, metric)])
        table = Table([cells], colWidths=[WIDTH * .46, WIDTH * .27, WIDTH * .27])
        table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), PALE), ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                   ('LEFTPADDING', (0, 0), (-1, -1), 10), ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                                   ('TOPPADDING', (0, 0), (-1, -1), 13), ('BOTTOMPADDING', (0, 0), (-1, -1), 13)]))
        self.story.extend([table, Spacer(1, 11)])

    def main(self):
        d, total = self.d, self.d['total']
        nominal, real = self.variation(total, False), self.variation(total, True)
        social = next(r for r in d['functions'] if r['name'] == 'Seguridad Social')
        interest = next(r for r in d['purposes'] if r['id'] == '5')
        self.section('01 / Lectura central', 'Presupuesto Nacional 2027', 'ONP: proyecto 2027 y cuadros comparativos. Presupuesto Abierto: crédito 2026. INDEC: IPC.', first=True)
        self.note(f"Administración Nacional · Proyecto de ley · Datos revisados el {date(d['meta']['reviewed'])}")
        self.add('El gasto crece. La inflación achica esa suba.' if nominal > 0 and real > 0 else 'El presupuesto pierde poder de compra.' if real < 0 else 'El poder de compra del presupuesto se mantiene.', 'lead')
        self.key_figures(total['project'], nominal, real)
        self.note(f"Gasto propuesto en {self.units.lower()}. Cambios frente a {self.base_label.lower()}. Cambio real: ajustado por inflación según el escenario del tablero.")
        self.add(f"El proyecto propone gastar <b>{money(total['project'])} en pesos corrientes</b>. Frente a {self.base_prose}, el monto {'sube' if nominal >= 0 else 'baja'} {num(abs(nominal))}%. Cuando se descuenta la inflación prevista, {'la suba queda en' if real >= 0 else 'el poder de compra cae'} <b>{num(abs(real))}%</b>.")
        self.add(f"La seguridad social concentra <b>{pct(ratio(social['project'], total['project']))}</b> del gasto y los intereses y gastos de la deuda, otro <b>{pct(ratio(interest['project'], total['project']))}</b>. Esa composición le pone un límite al margen para reasignar recursos. Una parte grande del presupuesto está vinculada con prestaciones y compromisos financieros; el resto tiene que sostener las demás políticas públicas.")
        self.add('El dato agregado no alcanza. Hay que mirar qué partidas ganan poder de compra y cuáles lo pierden. Que una partida suba no significa automáticamente que el servicio mejore. Puede haber más cobertura, mayores costos o simplemente una base muy baja.')
        self.callout('La conclusión', 'Para evaluar este presupuesto hay tres datos que importan. Cuánto compra cada partida, con qué ingresos se financia y cuánto se ejecuta. Si la inflación supera lo previsto, los recursos alcanzan para menos. Si la recaudación queda corta, el Gobierno tendrá que ajustar gastos, buscar financiamiento o postergar pagos.')
        self.note(f"Cuadros en {self.units.lower()}. Comparación con {self.base_prose}. Alcance nacional. El escenario de inflación se explica en Método y fuentes.")

        self.section('02 / Prioridades', 'Dónde se concentra el gasto', 'ONP: cuadro 2, finalidades y funciones. Temas: agrupación editorial del tablero.')
        self.add('Por cada $100 del proyecto, esta es la distribución por temas. La participación muestra cuánto recibe cada área del total. La variación real muestra si esos recursos compran más o menos que en 2026.')
        self.bars([(r['name'], r['project']) for r in sorted(d['topics'], key=lambda r: -r['project'])], total['project'])
        self.add('Las cinco finalidades oficiales', 'heading')
        self.table(['Finalidad', 'Proyecto 2027', 'Peso', 'Cambio de peso'],
                   [[r['name'], num(self.value(r['project']), 0), pct(ratio(r['project'], total['project'])),
                     num(ratio(r['project'], total['project']) - ratio(r[self.base], total[self.base])) + ' pp'] for r in d['purposes']],
                   [WIDTH - 212, 92, 54, 66])
        self.note(f"Montos en millones · {self.units}. pp = puntos porcentuales: pasar de 10% a 12% implica subir 2 pp. Temas y finalidades son distintas aperturas del mismo total; no se suman.")
        self.add('El peso de una finalidad puede aumentar aunque su monto real caiga, si otras partidas caen más. Por eso hay que mirar participación y variación real al mismo tiempo. Seguridad social incluye jubilaciones, pensiones y otras prestaciones; deuda pública aquí comprende intereses y gastos, no devolución del capital.')

        self.section('03 / Organismos', 'Quién administra los recursos', 'ONP: cuadro 4. Presupuesto Abierto: crédito anual 2026. INDEC y escenario ONP: ajuste anual.')
        self.add('La apertura por jurisdicción muestra quién administra esos recursos. Un cambio de estructura puede trasladar políticas de un organismo a otro y alterar la comparación.')
        self.comparison_table(d['jurisdictions'])
        comparable = [r for r in d['functions'] if finite(r.get(self.base)) and finite(r.get('project'))]
        increases = sorted(comparable, key=lambda r: self.value(r['project']) - self.value(r[self.base], 2026), reverse=True)
        up = [r for r in increases if self.value(r['project']) > self.value(r[self.base], 2026)][:3]
        down = [r for r in reversed(increases) if self.value(r['project']) < self.value(r[self.base], 2026)][:3]
        self.add('Qué movimientos explican el cambio', 'heading')
        for label, rows in [('Mayores aumentos de monto', up), ('Mayores reducciones de monto', down)]:
            detail = '; '.join(f"{escape(r['name'])}: {money(abs(self.value(r['project']) - self.value(r[self.base], 2026)))}" for r in rows) or 'No hay partidas comparables en esta dirección.'
            self.add(f'<b>{label}:</b> {detail}.', 'small')
        self.note('Ranking por diferencia absoluta de las funciones, en la unidad elegida. s/d = sin dato; s/c = sin comparación.')

        self.section('04 / Funciones', 'Qué políticas ganan o pierden', 'ONP: cuadro 2. Presupuesto Abierto: crédito anual 2026. INDEC y escenario ONP: ajuste anual.')
        self.add('La función identifica para qué se usa el dinero. La comparación real muestra cuánto cambia su poder de compra, una vez descontada la inflación.')
        self.comparison_table(d['functions'], compact=True)
        self.note('Partidas del proyecto 2027. Para estimar su efecto sobre la cobertura hacen falta el costo y la cantidad prevista de cada prestación.')

        self.section('05 / Programas', 'Del organismo a la política concreta', 'ONP: planilla 7 y fascículos por organismo. Presupuesto Abierto: nombres, organismos y códigos verificados.')
        self.add(f"El proyecto contiene {len(d['programs'])} partidas de programas. Estas son las 12 de mayor monto. El anexo opcional incluye el listado completo, con su organismo y la página del documento oficial.")
        largest = sorted(d['programs'], key=lambda r: -r['project'])[:12]
        self.table(['Programa / organismo', 'Proyecto 2027', 'Peso total', 'Cambio real'],
                   [[r['name'] + ' / ' + r['entity'], num(self.value(r['project']), 0), pct(ratio(r['project'], total['project'])), pct(self.variation(r, True), True)] for r in largest],
                   [WIDTH - 207, 88, 53, 66], compact=True)
        self.note(f"Montos en millones · {self.units}. Base de comparación: {self.base_label}. Se mantiene separada cada fila del documento oficial, incluso cuando dos nombres coinciden.")
        self.note('<link href="https://tablero.federicopellegrini.com.ar/nacion/#metodo">Correspondencias, cambios de alcance y documentos oficiales</link>')
        self.add('Cómo leer esta selección', 'heading')
        self.add(f"Podemos comparar {d['meta']['program_join_matched']} de las {len(d['programs'])} partidas con 2026. En las otras {len(d['programs']) - d['meta']['program_join_matched']}, las tareas se reorganizan y no se publica cómo distribuir todos los costos anteriores. Por eso, el anexo compara cinco conjuntos de programas: permite ver cuánto cambia su presupuesto sin confundir un traslado interno con un recorte.")
        if self.base == 'closing':
            self.callout('Por qué no aparece la variación de los programas', 'La planilla programática no publica el cierre estimado 2026. Ese dato sí existe para funciones y jurisdicciones. Para comparar programas, el informe puede exportarse con la base Inicial o Vigente 2026.')
        else:
            self.callout('Qué mirar para evaluar una política', 'Para evaluar una política no alcanza con mirar la partida. Hay que ver cuánta gente atiende, cuánto cuesta cada prestación y cuánto se ejecuta.')

        self.section('06 / Territorio', 'Qué se localiza en cada provincia', 'ONP: cuadro 6, ubicación geográfica; planilla 12, partidas de proyectos de inversión.')
        self.add('La ubicación registra dónde se imputa el gasto nacional. No equivale a una transferencia al gobernador ni identifica necesariamente dónde viven todos los beneficiarios. Las obras son una parte del gasto de cada ubicación: no deben sumarse a él.')
        works = {r['name']: r['project'] for r in d['works_geographies']}
        self.table(['Provincia o ubicación', 'Gasto 2027', 'Peso del gasto', 'Proyectos 2027'],
                   [[r['name'], num(self.value(r.get('project')), 0), pct(ratio(r.get('project'), total['project'])), num(self.value(works.get(r['name'])), 0)] for r in d['geographies']],
                   [WIDTH - 252, 92, 70, 90], compact=True)
        self.note(f"Montos en millones · {self.units}. Proyectos: total oficial por ubicación. El listado comprende {len(d['works'])} partidas por {money(self.value(d['works_total']))}; puede incluir equipamiento y una misma obra en varias ubicaciones. No es toda la inversión pública. Una celda sin dato no se completa con cero.")

        self.section('07 / Ingresos y economía', 'Con qué recursos se sostiene', 'ONP: cuadro 8, recursos; Mensaje 2027, supuestos macroeconómicos.')
        self.add(f"El proyecto estima <b>{money(self.value(d['resources_total']))}</b> de ingresos corrientes y de capital. Se apoya principalmente en impuestos y aportes a la seguridad social. Si la recaudación queda por debajo de lo previsto, el Gobierno tiene menos margen para sostener ese gasto.")
        self.table(['Recurso', 'Proyecto 2027', 'Peso'], [[r['name'], num(self.value(r['project']), 0), pct(ratio(r['project'], d['resources_total']))] for r in sorted(d['resources'], key=lambda r: -r['project'])], [WIDTH - 150, 95, 55], compact=True)
        self.note(f"Montos en millones · {self.units}. Incluye rentas de la propiedad. No es el total consolidado del Mensaje, que excluye rentas del FGS y del BCRA.")
        self.add('El escenario que supone el Gobierno', 'heading')
        self.table(['Variable', '2025', '2026', '2027'], [[r['name'], *[(('$' if r['unit'] == 'ARS/USD' else '') + num(v) + ('%' if r['unit'] == '%' else '')) for v in r['values']]] for r in d['macro']], [WIDTH - 189, 63, 63, 63], compact=True)
        self.note('2025: datos reportados por el Mensaje. 2026 y 2027: proyecciones oficiales. Inflación y dólar: diciembre; crecimiento: promedio anual. FGS = Fondo de Garantía de Sustentabilidad; BCRA = Banco Central.')
        contrib = next(r for r in d['resources'] if r['name'].startswith('Aportes'))
        self.add(f"Los aportes y contribuciones equivalen al {pct(ratio(contrib['project'], social['project']))} del gasto de la función Seguridad Social. Para cubrir la diferencia hacen falta impuestos y otros recursos. Esta comparación abarca toda la función Seguridad Social, no sólo ANSES.", 'small')

        self.section('08 / Ejecución', 'Qué parte del presupuesto se usó', f"Presupuesto Abierto: crédito anual y mensual 2026, corte {date(d['meta']['execution_cutoff'])}. INDEC: IPC mensual observado.")
        ex = d['execution'][0]
        accrued = sum(m['accrued'] for m in ex['months'])
        self.add(f"Al {date(d['meta']['execution_cutoff'])} se devengó el <b>{pct(ratio(accrued, ex['current']))}</b> del crédito vigente: {money(accrued)} sobre {money(ex['current'])}, en pesos corrientes. Devengar significa reconocer una obligación de pago; no significa necesariamente haberla pagado.")
        self.table(['Jurisdicción', 'Vigente', 'Devengado', 'Ejecución'],
                   [[r['name'], num(r['current'], 0), num(sum(m['accrued'] for m in r['months']), 0), pct(ratio(sum(m['accrued'] for m in r['months']), r['current']))] for r in d['execution'][1:]],
                   [WIDTH - 231, 86, 86, 59], compact=True)
        self.note('Cuadro por jurisdicción: millones de pesos corrientes. El porcentaje siempre divide devengado nominal por vigente nominal; no cambia al elegir precios constantes.')
        self.add('El recorrido mensual del total', 'heading')
        self.table(['Mes 2026', 'Gasto del mes', 'Acumulado / vigente'],
                   [[MONTHS[m['month'] - 1] + (' (parcial)' if m['partial'] else ''), num(m['real'] if self.mode == 'real' else m['accrued'], 0), pct(ratio(sum(x['accrued'] for x in ex['months'][:i+1]), ex['current']))] for i, m in enumerate(ex['months'])],
                   [WIDTH - 235, 105, 130], compact=True)
        self.note(f"Gasto mensual en millones · {self.units}. Septiembre llega al 15/09 y no es un mes completo. En reales, septiembre queda sin monto porque aún falta su IPC observado. No se usa una proyección para medir gasto real ejecutado.")
        self.note('Cuando una partida se ejecuta menos de lo previsto, hay que revisar qué prestación u obra quedó pendiente y si cambió su calendario.')

        self.section('09 / Historia y lectura final', 'Mirar más allá de un solo año', 'Presupuesto Abierto: totales anuales de ejecución. ONP: proyecto 2027. INDEC: IPC; 2026-2027, escenario.')
        self.add('Entre 2023 y 2025 se muestra el gasto reconocido al cierre de cada año. En 2026, el presupuesto vigente; en 2027, el proyecto. La diferencia entre una autorización y su ejecución importa porque parte de lo aprobado puede quedar sin usar.')
        self.table(['Año / etapa', 'Monto'], [[str(r['year']) + ' / ' + r['stage'], num(self.value(r['amount'], r['year']), 0)] for r in d['history']], [WIDTH - 130, 130])
        self.note(f"Montos en millones · {self.units}. Serie de totales de ejecución de Presupuesto Abierto. El alcance de la historia desde 2007 se detalla en el capítulo 15.")
        self.add('La historia completa y la gestión actual', 'heading')
        self.add('Los capítulos siguientes muestran cuánto se cobró y pagó en 2026, cuándo vence la deuda y qué fondos llegaron a las provincias. También comparan las prestaciones previstas con las realizadas y el gasto en obras con su avance físico. La serie de presupuestos y ejecución comienza en 2007.')
        self.add('Qué recomendamos seguir', 'heading')
        self.add('<b>El poder de compra de las partidas.</b> Si los precios suben más que los montos autorizados, se achica la capacidad de financiar las prestaciones. Hay que seguir ambos junto con la cantidad de personas atendidas.')
        self.add('<b>La recaudación que respalda el gasto.</b> Menos actividad o empleo formal pueden reducir los impuestos y los aportes previstos. Si eso ocurre, el Gobierno deberá decidir qué gastos sostiene y cómo los financia.')
        self.add('<b>La ejecución y sus resultados.</b> La autorización expresa una prioridad presupuestaria. Para saber si se convirtió en una política efectiva, hay que mirar obligaciones reconocidas, pagos, obras realizadas y población atendida.')
        self.callout('La lectura final', f"El proyecto {'amplía' if real >= 0 else 'reduce'} el poder de compra total frente a {self.base_prose}, según el escenario de inflación utilizado. Ese cambio se reparte de forma desigual entre las partidas. Recomendamos seguir qué áreas ganan recursos y cuánto de lo aprobado se convierte en prestaciones y obras. Ahí se ve realmente qué prioridades sostiene el Gobierno.")

        self.section('10 / Método y fuentes', 'Cómo se construyó el informe', 'Fuentes primarias enlazadas en esta página. Mismo corte y base de datos que el tablero.')
        self.add('Qué incluye', 'heading')
        self.add('Administración Nacional: administración central, organismos descentralizados y seguridad social. Se analizan gastos corrientes y de capital, sin aplicaciones financieras ni gastos figurativos. Se incluyen intereses entre organismos, como en los cuadros estadísticos del proyecto.', 'small')
        self.add('Cómo se descuenta la inflación', 'heading')
        self.add('Pesos corrientes son los montos de cada año. Pesos constantes expresan cuánto representarían con los precios de agosto de 2026. Para presupuestos anuales se divide por el IPC promedio del año y se multiplica por el IPC de agosto de 2026. Para la ejecución mensual se utiliza el IPC de cada mes.', 'small')
        self.add(f"El IPC del INDEC está observado hasta agosto de 2026. Para completar 2026 y 2027, el tablero construye una senda mensual uniforme compatible con los supuestos de inflación de diciembre del Mensaje: {num(d['deflator']['assumptions']['inflation_dec_2026'], 0)}% y {num(d['deflator']['assumptions']['inflation_dec_2027'], 0)}%, respectivamente. Esa senda es una elaboración propia; no una proyección mensual oficial. Los resultados reales futuros dependen de este escenario.", 'small')
        self.add('Las bases de comparación', 'heading')
        self.add('<b>Inicial:</b> crédito de inicio de 2026. <b>Vigente:</b> crédito autorizado con sus modificaciones al corte. <b>Cierre estimado:</b> proyección anual 2026 de los cuadros de la ONP. <b>Devengado:</b> obligaciones reconocidas. El proyecto 2027 todavía no es una ley sancionada ni gasto ejecutado.', 'small')
        self.add('Fuentes para consultar', 'heading')
        for file, label in [('mensaje2027.pdf', 'Mensaje: escenario macroeconómico'), ('cap1cu02.pdf', 'Cuadro 2: finalidades y funciones'), ('cap1cu04.pdf', 'Cuadro 4: jurisdicciones'), ('cap1cu06.pdf', 'Cuadro 6: ubicación geográfica'), ('cap1cu08.pdf', 'Cuadro 8: recursos'), ('cap1pla7.pdf', 'Planilla 7: programas'), ('cap1pl12.pdf', 'Planilla 12: proyectos de inversión'), ('credito-anual-2026.zip', 'Presupuesto Abierto: crédito anual 2026'), ('credito-mensual-2026.zip', 'Presupuesto Abierto: ejecución mensual 2026'), ('totales-de-presupuesto.zip', 'Presupuesto Abierto: totales históricos de ejecución')]:
            url = next(s['url'] for s in d['sources'] if s['file'] == file)
            self.add(f'<link href="{escape(url)}" color="#254b73">{escape(label)}</link>', 'small')
        self.add('<link href="https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-5-31" color="#254b73">INDEC: índice de precios al consumidor</link>', 'small')
        self.note('s/d = sin dato; s/c = sin comparación. Los importes ausentes no se sustituyen por cero. Los PDF oficiales redondean a millones: puede haber pequeñas diferencias entre sumas y totales. Programas: +1 millón; proyectos: +6 millones frente a los totales oficiales, antes de ajustar precios.')
        self.note(f'<link href="{SITE}" color="#254b73">Abrir el tablero nacional</link> · Allí se puede cambiar la comparación y consultar los datos completos. Informe elaborado por Federico Pellegrini a partir de las fuentes indicadas.')
        return self.story

    def comparison_table(self, rows, compact=False):
        self.table(['Área', BASES[self.base], 'Proyecto 2027', 'Cambio real'],
                   [[r['name'], num(self.value(r.get(self.base), 2026), 0), num(self.value(r.get('project')), 0), pct(self.variation(r, True), True)] for r in sorted(rows, key=lambda r: -(r.get('project') or 0))],
                   [WIDTH - 237, 86, 86, 65], compact=compact)
        self.note(f"Montos en millones · {self.units}. La variación real usa el IPC promedio anual y el escenario 2026-2027. Base: {self.base_label}.")

    def appendix(self):
        d = self.d
        self.section('Anexo / Programas', 'Todas las partidas programáticas', 'ONP: planilla 7; Presupuesto Abierto: crédito anual 2026. Referencia al final de cada nombre: página del PDF oficial.')
        self.note(f"{len(d['programs'])} filas · Montos en millones · {self.units}. Base: {self.base_label}. s/c indica falta de comparación verificada; no significa programa nuevo. Capital es un componente del proyecto, no se suma a él.")
        rows = []
        for r in d['programs']:
            context = ' · Actos electorales: 99,3% del proyecto (ONP J25, p. 109).' if r.get('comparison_context') else ''
            if r['id'] == 'p221':
                context += ' · Base sin garrafas; incluye BIRF 9521, con cierre fijado al 20/12/2026.'
            if not r['matched']:
                context += ' · Alcance reorganizado; ver revisión en el tablero.'
            rows.append([f"{r['id']} · {r['name']}{context}\n{r['entity']} / {r['jurisdiction']} · p. {r['page']}", num(self.value(r.get(self.base), 2026), 0), num(self.value(r['project']), 0), num(self.value(r['capital']), 0), pct(self.variation(r, True), True)])
        self.table(['Programa / organismo / referencia', BASES[self.base], 'Proyecto', 'Capital', 'Cambio real'], rows, [WIDTH - 257, 69, 72, 63, 53], compact=True)
        self.section('Anexo / Reorganizaciones', 'Comparar el conjunto', 'ONP: fascículos 2026 y 2027. Presupuesto Abierto: crédito anual al 15/09/2026. Reagrupación propia de partidas oficiales.')
        self.add('Cuando las tareas pasan de un programa a otro, comparar sólo sus nombres puede mostrar un recorte que es un traslado. Estos conjuntos mantienen juntas las áreas que se reorganizan. Incluyen las partidas del anexo anterior: no deben sumarse a ellas.')
        self.table(['Conjunto', BASES[self.base], 'Proyecto 2027', 'Cambio real'],
                   [[g['name'], num(self.value(g.get(self.base), 2026), 0), num(self.value(g['project']), 0), pct(self.variation(g, True), True)] for g in d['program_join']['groups']],
                   [WIDTH - 230, 80, 80, 70], compact=True)
        self.note(f'Montos en millones · {self.units}. Base: {self.base_label}. El cierre estimado no está publicado para estos conjuntos.')
        for g in d['program_join']['groups']:
            self.add(f"<b>{escape(g['name'])}.</b> {escape(g['note'])}", 'small')
        self.note('<link href="https://tablero.federicopellegrini.com.ar/nacion/#metodo">Ver la revisión de los 20 casos y sus documentos oficiales</link>')
        closure = next((e for e in d['program_join'].get('legal_evidence', []) if 'p221' in e['ids']), None)
        if closure:
            self.note(f'<link href="{escape(closure["url"])}">Energía: enmienda del Banco Mundial que fija el cierre del BIRF 9521.</link>')
        self.section('Anexo / Proyectos', 'Todas las partidas de inversión', 'ONP: planilla 12. Referencia al final de cada descripción: página del PDF oficial.')
        self.note(f"{len(d['works'])} partidas · Montos en millones · {self.units}. Una misma obra puede figurar en más de una ubicación. Incluye equipamiento; no es un censo de obras físicas distintas.")
        self.table(['Proyecto / organismo / referencia', 'Ubicación', 'Proyecto 2027'],
                   [[f"{r['id']} · {r['name']}\n{r['entity']} / {r['jurisdiction']} · p. {r['page']}", r['province'], num(self.value(r['project']), 0)] for r in d['works']],
                   [WIDTH - 165, 90, 75], compact=True)
        self.section('Anexo / Ejecución mensual', 'El detalle de cada jurisdicción', f"Presupuesto Abierto: crédito mensual 2026 al {date(d['meta']['execution_cutoff'])}. INDEC: IPC observado.")
        self.note(f"Montos del mes en millones · {self.units}. Acumulado / vigente: porcentaje nominal. Septiembre parcial hasta el 15/09, sin IPC observado para expresarlo en reales.")
        rows = []
        for r in d['execution']:
            cum = 0
            for m in r['months']:
                cum += m['accrued']
                rows.append([r['name'], MONTHS[m['month'] - 1] + (' (parcial)' if m['partial'] else ''), num(m['real'] if self.mode == 'real' else m['accrued'], 0), pct(ratio(cum, r['current']))])
        self.table(['Jurisdicción', 'Mes', 'Gasto del mes', 'Acum. / vigente'], rows, [WIDTH - 236, 93, 82, 61], compact=True)

    def footer(self, canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(LINE)
        canvas.line(42, 66, PAGE_W - 42, 66)
        text = self.p(getattr(canvas, '_report_source', ''), 'small')
        text.wrap(WIDTH, 30)
        text.drawOn(canvas, 42, 43)
        canvas.setFont('ManropeBold', 8)
        canvas.setFillColor(INK)
        canvas.drawString(42, 24, 'Federico Pellegrini')
        canvas.setFont('Manrope', 7)
        canvas.setFillColor(MUTED)
        label = 'tablero.federicopellegrini.com.ar/nacion/'
        canvas.drawCentredString(PAGE_W / 2 + 22, 24, label)
        canvas.linkURL(SITE, (190, 18, 420, 33), relative=0)
        canvas.drawRightString(PAGE_W - 42, 24, f'Página {doc.page}')
        canvas.restoreState()

    def header(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('ManropeBold', 9)
        canvas.setFillColor(TEAL)
        canvas.drawString(42, PAGE_H - 31, 'PELLEGRINI / PRESUPUESTO NACIONAL')
        canvas.setFont('Manrope', 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawRightString(PAGE_W - 42, PAGE_H - 31, self.units + ' · ' + BASES[self.base])
        canvas.restoreState()

    def build(self, path, full=False, focus=None):
        from national_decision_report import append_decisions
        decisions=json.loads((ROOT / 'nacion/data/decisions.json').read_text(encoding='utf-8'))
        if focus is None:
            self.main()
            from national_management_report import append_management
            append_management(self, json.loads((ROOT / 'nacion/data/gestion.json').read_text(encoding='utf-8')))
        if focus and focus.startswith('provincia-'):
            from national_territory_report import province_page
            province_page(self,json.loads((ROOT/'nacion/data/gestion.json').read_text(encoding='utf-8')),int(focus.split('-')[1]))
        else:
            append_decisions(self,decisions,focus)
        if full:
            self.appendix()
        doc = BaseDocTemplate(str(path), pagesize=A4, leftMargin=42, rightMargin=42, topMargin=56, bottomMargin=82,
                                title='Presupuesto Nacional 2027 - Informe completo', author='Federico Pellegrini',
                                subject=self.units + ' / ' + self.base_label, invariant=1, pageCompression=1)
        # A page template end callback ensures source notes follow tables across page breaks.
        from reportlab.platypus import PageTemplate, Frame
        frame = Frame(42, 82, WIDTH, PAGE_H - 138, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        doc.addPageTemplates(PageTemplate(id='Report', frames=frame, onPage=self.header, onPageEnd=self.footer))
        doc.build(self.story)

def fingerprint():
    return {name: hashlib.sha256((ROOT / name).read_bytes().replace(b'\r\n', b'\n') if name.endswith(('.py', '.json')) else (ROOT / name).read_bytes()).hexdigest() for name in INPUTS}

def run(output=OUT, check=False):
    manifest_file = output / 'manifest.json'
    if check:
        manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
        if manifest['inputs'] != fingerprint():
            raise ValueError('El informe nacional debe regenerarse: cambió un dato, fuente, cálculo o diseño.')
        for entry in manifest['reports']:
            for kind in ['main', 'full']:
                item = entry[kind]
                path = output / item['file']
                if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256'] or len(PdfReader(path).pages) != item['pages']:
                    raise ValueError('El PDF no coincide con el catálogo: ' + item['file'])
        for item in manifest['focused'] + manifest['territories']:
            path=output/item['file']
            assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256'] and len(PdfReader(path).pages)==item['pages']
        print('Informes nacionales: 12 versiones generales, 3 fichas temáticas y 24 provinciales verificadas.')
        return manifest
    register_fonts()
    data = json.loads((ROOT / 'nacion/data/budget.json').read_text(encoding='utf-8'))
    output.mkdir(parents=True, exist_ok=True)
    manifest = {'reviewed': data['meta']['reviewed'], 'execution_cutoff': data['meta']['execution_cutoff'], 'inputs': fingerprint(), 'reports': []}
    for mode in ['nominal', 'real']:
        for base in BASES:
            entry = {'price': mode, 'base': base}
            for kind in ['main', 'full']:
                filename = f'informe-nacional-{mode}-{base}' + ('-anexo' if kind == 'full' else '') + '.pdf'
                path = output / filename
                Report(data, mode, base).build(path, full=kind == 'full')
                entry[kind] = {'file': filename, 'pages': len(PdfReader(path).pages), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
                print(filename, entry[kind]['pages'], 'páginas')
            manifest['reports'].append(entry)
    manifest['focused']=[]
    for focus in ['inmunizaciones','educacion-superior','reactor-ra10']:
        filename=f'ficha-nacional-{focus}.pdf';path=output/filename
        Report(data,'nominal','current').build(path,focus=focus)
        manifest['focused'].append({'scope':focus,'file':filename,'pages':len(PdfReader(path).pages),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        print(filename,manifest['focused'][-1]['pages'],'páginas')
    manifest['territories']=[]
    management=json.loads((ROOT/'nacion/data/gestion.json').read_text(encoding='utf-8'))
    for province in management['provinces']['comparison']:
        province_id=province['provincia_id'];focus=f'provincia-{province_id}'
        filename=f'ficha-nacional-{focus}.pdf';path=output/filename
        Report(data,'nominal','current').build(path,focus=focus)
        pages=len(PdfReader(path).pages)
        assert pages==1, f'La ficha de {province["provincia"]} debe ocupar una página'
        manifest['territories'].append({'province_id':province_id,'province':province['provincia'],'file':filename,'pages':pages,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return manifest

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUT)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    run(args.output, args.check)

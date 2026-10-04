"""Engrave the editable B-flat soprano part as vector A4 PDF, SVG and MusicXML.

Usage: python scripts/build_score.py
Requires verovio, cairosvg, pypdf, reportlab and pdftoppm.
All notes and editorial octave choices are in scores/juebieshu.json.
"""
from pathlib import Path
import io
import json
import os
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET

import cairosvg
import verovio
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'site/scores/juebieshu'
DATA = ROOT / 'scores/juebieshu.json'
DURATIONS = {'w': 16, 'h': 8, 'q': 4, 'e': 2, 's': 1}
TYPES = {'w': 'whole', 'h': 'half', 'q': 'quarter', 'e': 'eighth', 's': '16th'}
# A perfect fourth changes the input notation to B-flat soprano notation.
SPELLING = {'C#': ('F', 1), 'D': ('G', 0), 'E': ('A', 0),
            'F#': ('B', 0), 'G': ('C', 0), 'A': ('D', 0), 'B': ('E', 0)}
PITCH_CLASSES = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
PAGES = [(1, 36), (37, 72), (73, 109)]


def element(parent, tag, value=None, **attributes):
    child = ET.SubElement(parent, tag, {k.replace('_', '-'): str(v) for k, v in attributes.items()})
    if value is not None:
        child.text = str(value)
    return child


def parse_bar(text, measure, lower_interlude=True):
    result = []
    for token in text.split():
        pitch, rhythm = token.split(':')
        duration = DURATIONS[rhythm[0]] * (1.5 if '.' in rhythm else 1)
        assert duration == int(duration)
        note = {'duration': int(duration), 'type': TYPES[rhythm[0]], 'dot': '.' in rhythm,
                'start': '~' in rhythm, 'stop': '_' in rhythm, 'rest': pitch == 'R'}
        if not note['rest']:
            match = re.fullmatch(r'([A-G]#?)(\d)', pitch)
            original, octave = match[1], int(match[2])
            step, alter = SPELLING[original]
            new_octave = octave + (1 if original[0] in ('G', 'A', 'B') else 0)
            # The interlude is an explicit saxophone arrangement choice.
            if lower_interlude and 49 <= measure <= 64:
                new_octave -= 1
            note.update(step=step, alter=alter, octave=new_octave)
        result.append(note)
    assert sum(n['duration'] for n in result) == 16, (measure, text)
    return result


def beam_groups(notes):
    """Beam eighths/sixteenths within each quarter-note beat, excluding rests."""
    groups, group, offset = [], [], 0
    for i, note in enumerate(notes):
        short = note['type'] in ('eighth', '16th') and not note['rest']
        if not short or (offset % 4 == 0 and group):
            if len(group) > 1:
                groups.append(group)
            group = []
        if short:
            group.append(i)
        offset += note['duration']
    if len(group) > 1:
        groups.append(group)
    return groups


def musicxml(data, lower_interlude=True):
    score = ET.Element('score-partwise', version='4.0')
    work = element(score, 'work')
    element(work, 'work-title', '诀别书')
    ident = element(score, 'identification')
    element(ident, 'creator', '邓垚', type='composer')
    encoding = element(ident, 'encoding')
    element(encoding, 'software', 'SaxVoice / Verovio')
    parts = element(score, 'part-list')
    p = element(parts, 'score-part', id='P1')
    element(p, 'part-name', '')
    instr = element(p, 'score-instrument', id='I1')
    element(instr, 'instrument-name', 'Soprano Saxophone in B-flat')
    midi = element(p, 'midi-instrument', id='I1')
    element(midi, 'midi-channel', 1)
    element(midi, 'midi-program', 65)
    part = element(score, 'part', id='P1')
    rehearsal = {1: 'A', 25: 'B', 49: 'C', 65: 'D', 89: 'E', 105: 'F'}
    display_tempos = {1: 97, 25: 112, 49: 112, 65: 114, 89: 116, 101: 120, 105: 93, 107: 90}
    all_notes, previous = [], None
    for number, bar in enumerate(data['bars'], 1):
        measure = element(part, 'measure', number=number)
        if number in (37, 73):
            element(measure, 'print', new_page='yes')
        elif (number - 1) % 4 == 0 and number != 109:
            element(measure, 'print', new_system='yes')
        if number == 1:
            attributes = element(measure, 'attributes')
            element(attributes, 'divisions', 4)
            key = element(attributes, 'key')
            element(key, 'fifths', 1)
            element(key, 'mode', 'minor')
            time = element(attributes, 'time')
            element(time, 'beats', 4)
            element(time, 'beat-type', 4)
            clef = element(attributes, 'clef')
            element(clef, 'sign', 'G')
            element(clef, 'line', 2)
            transpose = element(attributes, 'transpose')
            element(transpose, 'diatonic', -1)
            element(transpose, 'chromatic', -2)
        if number in rehearsal:
            direction = element(measure, 'direction', placement='above')
            kind = element(direction, 'direction-type')
            element(kind, 'rehearsal', rehearsal[number])
        if number in display_tempos:
            direction = element(measure, 'direction', placement='above')
            kind = element(direction, 'direction-type')
            metro = element(kind, 'metronome')
            element(metro, 'beat-unit', 'quarter')
            element(metro, 'per-minute', display_tempos[number])
            element(direction, 'sound', tempo=display_tempos[number])
        notes = parse_bar(bar, number, lower_interlude)
        beams = {}
        for group in beam_groups(notes):
            for i, index in enumerate(group):
                beams[index] = [(1, 'begin' if i == 0 else 'end' if i == len(group)-1 else 'continue')]
                if notes[index]['type'] == '16th':
                    left = i > 0 and notes[group[i-1]]['type'] == '16th'
                    right = i < len(group)-1 and notes[group[i+1]]['type'] == '16th'
                    beams[index].append((2, 'continue' if left and right else 'end' if left else 'begin' if right else 'backward hook' if i else 'forward hook'))
        for i, n in enumerate(notes):
            # Validate both ends of every tie across bar and page boundaries.
            if n['stop']:
                assert previous and previous['start'] and not n['rest']
                assert (n['step'], n['alter'], n['octave']) == (previous['step'], previous['alter'], previous['octave']), number
            elif previous and previous['start']:
                raise ValueError(f'Unterminated tie before bar {number}')
            node = element(measure, 'note', id=f'm{number}n{i+1}')
            if n['rest']:
                element(node, 'rest')
            else:
                pitch = element(node, 'pitch')
                element(pitch, 'step', n['step'])
                if n['alter']:
                    element(pitch, 'alter', n['alter'])
                element(pitch, 'octave', n['octave'])
            element(node, 'duration', n['duration'])
            for state in ('stop', 'start'):
                if n[state]:
                    element(node, 'tie', type=state)
            element(node, 'type', n['type'])
            if n['dot']:
                element(node, 'dot')
            for level, value in beams.get(i, []):
                element(node, 'beam', value, number=level)
            if n['stop'] or n['start']:
                notation = element(node, 'notations')
                for state in ('stop', 'start'):
                    if n[state]:
                        element(notation, 'tied', type=state)
            previous = n
            all_notes.append(n)
        if number == 109:
            barline = element(measure, 'barline', location='right')
            element(barline, 'bar-style', 'light-heavy')
    assert not previous['start']
    ET.indent(score)
    return ET.tostring(score, encoding='utf-8', xml_declaration=True), all_notes


def page_overlay(page_number, first, last, lower_interlude=True):
    stream = io.BytesIO()
    pdf = canvas.Canvas(stream, pagesize=A4)
    width, height = A4
    pdf.setFillColorRGB(.15, .15, .15)
    pdf.setFont('Helvetica', 8)
    pdf.drawString(13*mm, height-13*mm, 'SAXVOICE / SOPRANO SAXOPHONE IN B-FLAT')
    pdf.drawRightString(width-13*mm, height-13*mm, f'{page_number} / 3')
    pdf.setFont('ScoreChinese', 23)
    pdf.drawString(13*mm, height-25*mm, '诀别书')
    pdf.setFont('ScoreChinese', 9)
    pdf.drawRightString(width-13*mm, height-25*mm, '作曲：邓垚  ·  降 B 高音萨克斯')
    pdf.setFont('ScoreChinese', 8)
    pdf.drawString(13*mm, height-34*mm, 'E 小调记谱（一个升号） · 实音 D 小调 · 4/4')
    pdf.drawRightString(width-13*mm, height-34*mm, f'第 {first}-{last} 小节')
    pdf.setStrokeColorRGB(.65, .65, .65)
    pdf.setLineWidth(.4)
    pdf.line(13*mm, height-38*mm, width-13*mm, height-38*mm)
    pdf.line(13*mm, 16*mm, width-13*mm, 16*mm)
    pdf.setFont('ScoreChinese', 7.5)
    pdf.drawString(13*mm, 11*mm, '主旋律移调编配 · C 段（49-64小节）降低八度衔接 · 速度随伴奏自然伸缩' if lower_interlude else '主旋律移调对照版 · 保留输入旋律音区 · 速度随伴奏自然伸缩')
    pdf.setFont('Helvetica', 7)
    pdf.drawRightString(width-13*mm, 7*mm, 'SaxVoice | 2026.10.05')
    pdf.showPage()
    pdf.save()
    stream.seek(0)
    return PdfReader(stream).pages[0]


def vector_tempos(svg, toolkit):
    namespace = {'s': 'http://www.w3.org/2000/svg'}
    root = ET.fromstring(svg)
    glyph = ET.fromstring((Path(toolkit.getResourcePath())/'Leipzig/ECA5.xml').read_text())[0].attrib['d']
    for group in root.findall('.//s:g[@class="tempo"]', namespace):
        text_node = group.find('s:text', namespace)
        if text_node is None:
            continue
        x, y = float(text_node.attrib['x']), float(text_node.attrib['y'])
        label = ''.join(text_node.itertext()).strip()
        tempo = re.search(r'(\d+)\s*$', label)[1]
        group.remove(text_node)
        ET.SubElement(group, '{http://www.w3.org/2000/svg}path', {
            'd':glyph, 'transform':f'translate({x},{y}) scale(.72,-.72)'})
        t = ET.SubElement(group, '{http://www.w3.org/2000/svg}text', {
            'x':str(x+330), 'y':str(y), 'font-size':'405px', 'font-family':'serif', 'font-weight':'bold'})
        t.text = '= ' + tempo
    ET.register_namespace('', namespace['s'])
    ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
    return ET.tostring(root, encoding='unicode')


def main():
    data = json.loads(DATA.read_text())
    DEST.mkdir(parents=True, exist_ok=True)
    font = os.environ.get('SAXVOICE_SCORE_FONT', '/System/Library/Fonts/STHeiti Light.ttc')
    pdfmetrics.registerFont(TTFont('ScoreChinese', font, subfontIndex=0))
    xml, notes = musicxml(data)
    (DEST/'juebieshu-soprano-bb.musicxml').write_bytes(xml)
    toolkit = verovio.toolkit()
    toolkit.setOptions({'pageWidth':2100,'pageHeight':2970,'scale':100,
                        'pageMarginTop':420,'pageMarginBottom':220,
                        'pageMarginLeft':130,'pageMarginRight':130,
                        'breaks':'encoded','header':'none','footer':'none','smuflTextFont':'none',
                        'spacingSystem':7,'systemMaxPerPage':9,
                        'spacingLinear':.18,'spacingNonLinear':.55,'minLastJustification':0})
    assert toolkit.loadData(xml.decode())
    page_count = toolkit.getPageCount()
    if page_count != 3:
        raise RuntimeError(f'Expected 3 pages, rendered {page_count}')
    writer = PdfWriter()
    pages = []
    for number, (first, last) in enumerate(PAGES, 1):
        svg = vector_tempos(toolkit.renderToSVG(number), toolkit)
        (DEST/f'notation-{number}.svg').write_text(svg)
        pdf_bytes = cairosvg.svg2pdf(bytestring=svg.encode(), scale=96/254)
        page = PdfReader(io.BytesIO(pdf_bytes)).pages[0]
        if abs(float(page.mediabox.width)-A4[0]) > .1:
            raise RuntimeError(f'Unexpected page dimensions {page.mediabox}')
        page.merge_page(page_overlay(number, first, last))
        writer.add_page(page).compress_content_streams()
        pages.append({'number':number,'firstMeasure':first,'lastMeasure':last,'image':f'page-{number}.png'})
    writer.add_metadata({'/Title':'诀别书 - 降B高音萨克斯 - A4矢量谱',
                         '/Author':'作曲：邓垚；移调编配：SaxVoice',
                         '/Subject':'109小节；3页A4；E小调记谱；49-64小节降低八度'})
    pdf_path = DEST/'juebieshu-soprano-bb-a4.pdf'
    with pdf_path.open('wb') as stream:
        writer.write(stream)
    shutil.copyfile(pdf_path, DEST/'juebieshu-saxophone-a4.pdf')
    reference_xml, reference_notes = musicxml(data, lower_interlude=False)
    (DEST/'juebieshu-soprano-bb-reference.musicxml').write_bytes(reference_xml)
    assert toolkit.loadData(reference_xml.decode()) and toolkit.getPageCount() == 3
    reference_writer = PdfWriter()
    for number, (first, last) in enumerate(PAGES, 1):
        svg = vector_tempos(toolkit.renderToSVG(number), toolkit)
        page = PdfReader(io.BytesIO(cairosvg.svg2pdf(bytestring=svg.encode(), scale=96/254))).pages[0]
        page.merge_page(page_overlay(number, first, last, lower_interlude=False))
        reference_writer.add_page(page).compress_content_streams()
    reference_writer.add_metadata({'/Title':'诀别书 - 降B高音萨克斯 - 原谱音区移调对照版',
                                   '/Author':'作曲：邓垚；移调：SaxVoice',
                                   '/Subject':'109小节；3页A4；E小调记谱；保留输入旋律音区'})
    with (DEST/'juebieshu-soprano-bb-reference-a4.pdf').open('wb') as stream:
        reference_writer.write(stream)
    poppler = shutil.which('pdftoppm') or '/Users/zstar/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm'
    subprocess.run([poppler,'-scale-to','1800','-png',str(pdf_path),str(DEST/'page')],check=True)
    for path in DEST.glob('row-*.png'):
        path.unlink()
    (DEST/'page-4.png').unlink(missing_ok=True)
    pitches = [12*(n['octave']+1)+PITCH_CLASSES[n['step']]+n['alter'] for n in notes if not n['rest']]
    manifest = {'title':'诀别书','composer':'邓垚','instrument':'降 B 高音萨克斯',
                'writtenKey':'E minor','concertKey':'D minor','meter':'4/4',
                'updatedDate':'2026-10-05','paper':'A4','format':'vector PDF + MusicXML',
                'measureCount':109,'systemCount':27,'pages':pages,'pdf':pdf_path.name,
                'musicxml':'juebieshu-soprano-bb.musicxml','writtenMidiRange':[min(pitches),max(pitches)],
                'arrangementNote':'49-64小节降低八度；保留109小节与过渡段的节奏和位置。',
                'comparisonRecording':'https://music.163.com/song?id=2038191895',
                'verificationNote':'核对开头、49-64小节与段落回归；与原录音同调。单声部编配含八度选择，非钢琴双手逐音转录。'}
    (DEST/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(f'Created {page_count} A4 vector pages; {len(notes)} events; written MIDI range {min(pitches)}-{max(pitches)}')


if __name__ == '__main__':
    main()

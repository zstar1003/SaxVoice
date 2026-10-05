"""Build the data-driven SaxVoice library. Run after build_score.py for the base piece.
Dependencies: verovio, cairosvg, reportlab, pypdf; Poppler pdftoppm.
SAXVOICE_SCORE_FONT and SAXVOICE_PDFTOPPM may override local runtime paths.
"""
from pathlib import Path
import argparse
import copy
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
from build_score import element, vector_tempos, DURATIONS, TYPES, PITCH_CLASSES

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
LETTERS = 'CDEFGAB'
INSTRUMENTS = {
    'soprano': {'label':'高音', 'name':'降 B 高音萨克斯', 'english':'Soprano Saxophone in B-flat', 'program':65, 'diatonic':-1, 'chromatic':-2, 'octave':0},
    'alto': {'label':'中音', 'name':'降 E 中音萨克斯', 'english':'Alto Saxophone in E-flat', 'program':66, 'diatonic':-5, 'chromatic':-9, 'octave':0},
}
MAJOR = dict(zip(range(-7,8), [n+' 大调' for n in ('C♭','G♭','D♭','A♭','E♭','B♭','F','C','G','D','A','E','B','F♯','C♯')]))
MINOR = dict(zip(range(-7,8), [n+' 小调' for n in ('A♭','E♭','B♭','F','C','G','D','A','E','B','F♯','C♯','G♯','D♯','A♯')]))
DORIAN = dict(zip(range(-7,8), [n+' 多利亚' for n in ('D♭','A♭','E♭','B♭','F','C','G','D','A','E','B','F♯','C♯','G♯','D♯')]))


def key_name(fifths, mode):
    return {'major': MAJOR, 'minor': MINOR, 'dorian': DORIAN}[mode][fifths]


def midi(pitch):
    return 12*(int(pitch.findtext('octave'))+1)+PITCH_CLASSES[pitch.findtext('step')]+int(pitch.findtext('alter', '0'))


def shift(pitch, semitones, diatonic):
    old = midi(pitch)
    index = int(pitch.findtext('octave'))*7+LETTERS.index(pitch.findtext('step'))+diatonic
    octave, letter = divmod(index, 7)
    step = LETTERS[letter]
    alter = old+semitones-(12*(octave+1)+PITCH_CLASSES[step])
    assert abs(alter) <= 1, (old, step, octave, alter)
    pitch.clear()
    element(pitch, 'step', step)
    if alter:
        element(pitch, 'alter', alter)
    element(pitch, 'octave', octave)


def configure_instrument(root, instrument):
    info = INSTRUMENTS[instrument]
    root.find('.//score-instrument/instrument-name').text = info['english']
    root.find('.//midi-program').text = str(info['program'])
    attrs = root.find('.//attributes')
    old = attrs.find('transpose')
    if old is not None:
        attrs.remove(old)
    t = element(attrs, 'transpose')
    element(t, 'diatonic', info['diatonic'])
    element(t, 'chromatic', info['chromatic'])
    if info['octave']:
        element(t, 'octave-change', info['octave'])


def create_xml(piece):
    root = ET.Element('score-partwise', version='4.0')
    element(element(root, 'work'), 'work-title', piece['title'])
    ident = element(root, 'identification')
    element(ident, 'creator', piece['composer'], type='composer')
    element(ident, 'rights', piece['rights'])
    element(element(ident, 'encoding'), 'software', 'SaxVoice / Verovio')
    sp = element(element(root, 'part-list'), 'score-part', id='P1')
    element(sp, 'part-name', '')
    element(element(sp, 'score-instrument', id='I1'), 'instrument-name', '')
    mi = element(sp, 'midi-instrument', id='I1')
    element(mi, 'midi-channel', 1)
    element(mi, 'midi-program', 65)
    part = element(root, 'part', id='P1')
    capacity = piece['meter'][0]*16//piece['meter'][1]
    # Keep existing editions byte-identical; finer divisions only for 32nd notes.
    factor = 2 if any(':t' in bar for bar in piece['bars']) else 1
    durations = {**DURATIONS, 't': .5}
    types = {**TYPES, 't': '32nd'}
    previous = None
    for number, bar in enumerate(piece['bars'], 1):
        notes = []
        for token in bar.split():
            pitch, rhythm = token.split(':')
            n = dict(duration=durations[rhythm[0]]*(1.5 if '.' in rhythm else 1), type=types[rhythm[0]], dot='.' in rhythm, start='~' in rhythm, stop='_' in rhythm, rest=pitch=='R')
            if pitch != 'R':
                match = re.fullmatch(r'([A-G])([#b]?)(\d)', pitch)
                assert match, token
                n.update(step=match[1], alter={'':0, '#':1, 'b':-1}[match[2]], octave=int(match[3]))
            notes.append(n)
        expected = (piece['pickupTicks'] if number == 1 and piece['pickupTicks'] else piece['endingTicks'] if number == len(piece['bars']) and piece['endingTicks'] else capacity)
        assert sum(n['duration'] for n in notes) == expected, (piece['id'], number, bar)
        measure = element(part, 'measure', number=number, **({'implicit':'yes'} if expected != capacity else {}))
        # A pickup shares the first system with the next four full bars.
        start = 2 if piece['pickupTicks'] else 1
        if number > start and (number-start)%4 == 0:
            element(measure, 'print', **({'new_page':'yes'} if (number-start)%32==0 else {'new_system':'yes'}))
        if number == 1:
            attrs = element(measure, 'attributes')
            element(attrs, 'divisions', 4*factor)
            key = element(attrs, 'key')
            element(key, 'fifths', piece['concertKeyFifths'])
            element(key, 'mode', piece['mode'])
            time = element(attrs, 'time')
            element(time, 'beats', piece['meter'][0])
            element(time, 'beat-type', piece['meter'][1])
            clef = element(attrs, 'clef')
            element(clef, 'sign', 'G')
            element(clef, 'line', 2)
            direction = element(measure, 'direction', placement='above')
            metro = element(element(direction, 'direction-type'), 'metronome')
            element(metro, 'beat-unit', 'quarter')
            element(metro, 'per-minute', piece['tempo'])
            element(direction, 'sound', tempo=piece['tempo'])
        beams = {}
        # Group eighth-note meters in dotted-quarter beats (6 ticks).
        groups = compound_beams(notes, 6 if piece['meter'][1]==8 and piece['meter'][0]%3==0 else 4)
        for group in groups:
            for i, index in enumerate(group):
                beams[index] = [(1, 'begin' if i == 0 else 'end' if i == len(group)-1 else 'continue')]
                depth = {'eighth':1, '16th':2, '32nd':3}[notes[index]['type']]
                for level in range(2, depth+1):
                    eligible = ('16th','32nd') if level==2 else ('32nd',)
                    left = i > 0 and notes[group[i-1]]['type'] in eligible
                    right = i < len(group)-1 and notes[group[i+1]]['type'] in eligible
                    beams[index].append((level, 'continue' if left and right else 'end' if left else 'begin' if right else 'backward hook' if i else 'forward hook'))
        for index, n in enumerate(notes):
            if n['stop']:
                assert previous and previous['start'] and all(n[k]==previous[k] for k in ('step','alter','octave'))
            elif previous:
                assert not previous['start']
            node = element(measure, 'note')
            if n['rest']:
                element(node, 'rest')
            else:
                p = element(node, 'pitch')
                element(p, 'step', n['step'])
                if n['alter']:
                    element(p, 'alter', n['alter'])
                element(p, 'octave', n['octave'])
            ticks = n['duration']*factor
            assert ticks == int(ticks), (piece['id'], number, n)
            element(node, 'duration', int(ticks))
            for state in ('stop','start'):
                if n[state]:
                    element(node, 'tie', type=state)
            element(node, 'type', n['type'])
            if n['dot']:
                element(node, 'dot')
            for level, value in beams.get(index, []):
                element(node, 'beam', value, number=level)
            if n['stop'] or n['start']:
                notation = element(node, 'notations')
                for state in ('stop','start'):
                    if n[state]:
                        element(notation, 'tied', type=state)
            previous = n
        if number == len(piece['bars']):
            element(element(measure, 'barline', location='right'), 'bar-style', 'light-heavy')
    assert not previous['start']
    return root


def compound_beams(notes, beat_ticks=6):
    groups, group, offset = [], [], 0
    for i, n in enumerate(notes):
        short = n['type'] in ('eighth','16th','32nd') and not n['rest']
        if not short or (offset%beat_ticks==0 and group):
            if len(group)>1:
                groups.append(group)
            group=[]
        if short:
            group.append(i)
        offset += n['duration']
    if len(group)>1:
        groups.append(group)
    return groups


def display_accidentals(root):
    """MusicXML pitch/alter alone is playback-only in Verovio; spell visible signs."""
    fifths=int(root.findtext('.//key/fifths'))
    key={s:0 for s in LETTERS}
    for step in ('FCGDAEB' if fifths>=0 else 'BEADGCF')[:abs(fifths)]:
        key[step]=1 if fifths>=0 else -1
    for measure in root.findall('.//part/measure'):
        active={}
        for note in measure.findall('note'):
            pitch=note.find('pitch')
            if pitch is None:
                continue
            step=pitch.findtext('step'); octave=pitch.findtext('octave')
            alteration=int(pitch.findtext('alter','0'))
            old=note.find('accidental')
            if old is not None:
                note.remove(old)
            tied=any(t.get('type')=='stop' for t in note.findall('tie'))
            if not tied and alteration!=active.get((step,octave),key[step]):
                accidental=ET.Element('accidental')
                accidental.text={-1:'flat',0:'natural',1:'sharp'}[alteration]
                # MusicXML requires accidentals after the type and dots, before beams.
                index=list(note).index(note.find('type'))+1+len(note.findall('dot'))
                note.insert(index,accidental)
            active[(step,octave)]=alteration


def overlay(piece, instrument, key, number, total, first, last):
    stream = io.BytesIO()
    c = canvas.Canvas(stream, pagesize=A4)
    w,h = A4
    c.setFont('Helvetica', 8)
    c.drawString(13*mm,h-13*mm,'SAXVOICE / '+INSTRUMENTS[instrument]['english'].upper())
    c.setFont('ScoreChinese',24)
    c.drawString(13*mm,h-26*mm,piece['title'])
    c.setFont('ScoreChinese',9)
    c.drawString(13*mm,h-34*mm,piece['composer']+'  /  '+INSTRUMENTS[instrument]['name'])
    c.setFont('ScoreChinese',8)
    c.drawString(13*mm,h-40*mm,'记谱 '+key+'  ·  实音 '+piece['concertKey']+'  ·  '+piece['meterText'])
    c.setStrokeColorRGB(.7,.7,.7)
    c.line(13*mm,h-44*mm,w-13*mm,h-44*mm)
    c.setFont('ScoreChinese',8)
    c.drawString(13*mm,14*mm,('49–64小节保留已确认的八度处理。' if piece['id']=='juebieshu' else '单声部旋律版 · SaxVoice 移调排版'))
    c.setFont('Helvetica',8)
    c.drawRightString(w-13*mm,14*mm,f'A4 / {number} of {total} / bars {first}-{last}')
    c.save()
    return PdfReader(io.BytesIO(stream.getvalue())).pages[0]


def engrave(piece, root, instrument, previous=None):
    configure_instrument(root,instrument)
    fifths = int(root.findtext('.//key/fifths'))
    key = key_name(fifths,piece['mode'])
    pitches = [midi(p) for p in root.findall('.//note/pitch')]
    assert 58 <= min(pitches) <= max(pitches) <= 90, (piece['id'],instrument,min(pitches),max(pitches))
    destination = SITE/'scores'/piece['id']/instrument
    destination.mkdir(parents=True, exist_ok=True)
    ET.indent(root)
    xml = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    # Keep existing approved files whenever their generated notation is identical.
    if previous and (SITE/previous['musicxml']).read_bytes()==xml and all((SITE/p['image']).exists() for p in previous['pages']) and (SITE/previous['pdf']).exists():
        return copy.deepcopy(previous)
    (destination/'score.musicxml').write_bytes(xml)
    toolkit = verovio.toolkit()
    spacing=7 if piece['id']=='juebieshu' or piece['measureCount']>=29 else 18
    toolkit.setOptions({'pageWidth':2100,'pageHeight':2970,'scale':100,'pageMarginTop':480,'pageMarginBottom':220,'pageMarginLeft':130,'pageMarginRight':130,'breaks':'encoded','header':'none','footer':'none','smuflTextFont':'none','spacingSystem':spacing,'systemMaxPerPage':9,'spacingLinear':.18,'spacingNonLinear':.55,'minLastJustification':0})
    assert toolkit.loadData(xml.decode())
    count = toolkit.getPageCount()
    if piece['id']=='juebieshu':
        ranges=[(1,36),(37,72),(73,109)]
    else:
        start=2 if piece['pickupTicks'] else 1
        cuts=[1]+list(range(start+32,piece['measureCount']+1,32))+[piece['measureCount']+1]
        ranges=[(a,b-1) for a,b in zip(cuts,cuts[1:])]
    assert count==len(ranges), (piece['id'],count,ranges)
    writer = PdfWriter()
    pages=[]
    for number,(first,last) in enumerate(ranges,1):
        svg=vector_tempos(toolkit.renderToSVG(number),toolkit)
        page=PdfReader(io.BytesIO(cairosvg.svg2pdf(bytestring=svg.encode(),scale=96/254))).pages[0]
        page.merge_page(overlay(piece,instrument,key,number,count,first,last))
        writer.add_page(page).compress_content_streams()
        pages.append(dict(number=number,firstMeasure=first,lastMeasure=last,image=f'scores/{piece["id"]}/{instrument}/page-{number}.png'))
    writer.add_metadata({'/Title':piece['title']+' · '+INSTRUMENTS[instrument]['name'], '/Author':piece['composer']+' / SaxVoice', '/Subject':'A4 vector melody score'})
    path=destination/'score.pdf'
    with path.open('wb') as stream:
        writer.write(stream)
    executable=os.environ.get('SAXVOICE_PDFTOPPM') or shutil.which('pdftoppm') or '/Users/zstar/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm'
    subprocess.run([executable,'-scale-to','1800','-png',str(path),str(destination/'page')],check=True,stdout=subprocess.DEVNULL)
    # Poppler uses leading zeroes only for documents with >=10 pages; these have <=3.
    return dict(instrument=instrument,label=INSTRUMENTS[instrument]['name'],writtenKey=key,writtenMidiRange=[min(pitches),max(pitches)],soundingOctaveOffset=0 if instrument=='soprano' else -1,pdf=f'scores/{piece["id"]}/{instrument}/score.pdf',musicxml=f'scores/{piece["id"]}/{instrument}/score.musicxml',pages=pages)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rebuild',nargs='*',help='Re-engrave named pieces, or all pieces when no IDs are given; approved base soprano stays unchanged.')
    args=parser.parse_args()
    pdfmetrics.registerFont(TTFont('ScoreChinese',os.environ.get('SAXVOICE_SCORE_FONT','/System/Library/Fonts/STHeiti Light.ttc'),subfontIndex=0))
    manifest=json.loads((SITE/'scores/juebieshu/manifest.json').read_text())
    base=ET.parse(SITE/'scores/juebieshu/juebieshu-soprano-bb.musicxml').getroot()
    previous={p['id']:p['variants'] for p in json.loads((SITE/'catalog.json').read_text())['pieces']} if (SITE/'catalog.json').exists() else {}
    if args.rebuild is not None:
        previous={k:v for k,v in previous.items() if args.rebuild and k not in args.rebuild}
    jue=dict(id='juebieshu',title='诀别书',english='Jue Bie Shu',aliases='juebieshu juebie 诀别',composer='邓垚',genre='当代旋律',difficulty='进阶',mode='minor',concertKey='D 小调',meterText='4/4',measureCount=109,description='109 小节完整旋律，保留已确认的高音版；49–64 小节降低八度。',rights='经授权整理发布；音乐作品及原曲谱权利归原权利人。',variants={},comparisonRecording=manifest['comparisonRecording'],verificationNote=manifest['verificationNote'])
    # Keep the approved soprano files byte-for-byte.
    jue['variants']['soprano']=dict(instrument='soprano',label=INSTRUMENTS['soprano']['name'],writtenKey='E 小调',writtenMidiRange=manifest['writtenMidiRange'],soundingOctaveOffset=0,pdf='scores/juebieshu/juebieshu-soprano-bb-a4.pdf',musicxml='scores/juebieshu/juebieshu-soprano-bb.musicxml',pages=[{**p,'image':'scores/juebieshu/'+p['image']} for p in manifest['pages']],referencePdf='scores/juebieshu/juebieshu-soprano-bb-reference-a4.pdf')
    for instrument in ('alto',):
        root=copy.deepcopy(base)
        if instrument=='alto':
            for pitch in root.findall('.//note/pitch'):
                shift(pitch,-5,-3)
            root.find('.//key/fifths').text='2'
        jue['variants'][instrument]=engrave(jue,root,instrument,previous.get('juebieshu',{}).get(instrument))
    pieces=[jue]
    aliases={'amazing-grace':'qiyien dian qiyiendian 恩典','greensleeves':'lvxiuzi 绿袖','auld-lang-syne':'youyidijiutianchang 友谊','twinkle':'xiaoxingxing 星星','frere-jacques':'liangzhilaohu 两只 老虎','ode-to-joy':'huanlesong 贝多芬 Beethoven','brahms-lullaby':'yaolanqu 勃拉姆斯 Brahms'}
    for piece in json.loads((ROOT/'scores/library.json').read_text()):
        root=create_xml(piece)
        piece.update(concertKey=key_name(piece['concertKeyFifths'],piece['mode']),meterText='/'.join(map(str,piece['meter'])),measureCount=len(piece['bars']),aliases=piece.get('aliases',aliases.get(piece['id'],'')),variants={})
        for instrument in INSTRUMENTS:
            part=copy.deepcopy(root)
            semitones,diatonic=(2,1) if instrument!='alto' else (-3,-2)
            # Keep the alto part within the standard written B-flat3–F-sharp6 range.
            if instrument=='alto' and min(midi(p) for p in part.findall('.//note/pitch'))-3 < 58:
                semitones,diatonic=9,5
            for pitch in part.findall('.//note/pitch'):
                shift(pitch,semitones,diatonic)
            part.find('.//key/fifths').text=str(piece['concertKeyFifths']+(2 if instrument!='alto' else 3))
            display_accidentals(part)
            piece['variants'][instrument]=engrave(piece,part,instrument,previous.get(piece['id'],{}).get(instrument))
            piece['variants'][instrument]['soundingOctaveOffset']=(semitones+INSTRUMENTS[instrument]['chromatic']+12*INSTRUMENTS[instrument]['octave'])//12
        pieces.append({k:v for k,v in piece.items() if k not in ('bars','pickupTicks','endingTicks','concertKeyFifths','tempo','meter')})
        print(piece['title']+': 2 instrument editions')
    taxonomy=json.loads((ROOT/'scores/categories.json').read_text())
    group_ids=[group['id'] for category in taxonomy for group in category['groups']]
    assert len(group_ids)==len(set(group_ids)), 'Subcategory IDs must be unique'
    membership=[id for category in taxonomy for group in category['groups'] for id in group['pieces']]
    assert len(membership)==len(set(membership)), 'Duplicate category membership'
    assert set(membership)=={piece['id'] for piece in pieces}, 'Category membership must match the library'
    for piece in pieces:
        group=next((group for category in taxonomy for group in category['groups'] if piece['id'] in group['pieces']),None)
        assert group is not None, ('missing category',piece['id'])
        category=next(category for category in taxonomy if group in category['groups'])
        piece.update(category=category['id'],subcategory=group['id'])
    categories=[{**category,'groups':[{k:v for k,v in group.items() if k!='pieces'} for group in category['groups']]} for category in taxonomy]
    (SITE/'catalog.json').write_text(json.dumps(dict(version='grouped-v5',updatedDate='2026-10-05',instruments=INSTRUMENTS,categories=categories,pieces=pieces),ensure_ascii=False,indent=2)+'\n')
    print(f'Built {len(pieces)} pieces / {len(pieces)*len(INSTRUMENTS)} editions')


if __name__=='__main__':
    main()

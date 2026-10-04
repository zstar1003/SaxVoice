"""Verify all published score assets, instrument transposition, rhythms and ties."""
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from pypdf import PdfReader
from reportlab.lib.pagesizes import A4

SITE=Path(__file__).resolve().parents[1]/'site'
PC={'C':0,'D':2,'E':4,'F':5,'G':7,'A':9,'B':11}
def events(path):
    root=ET.parse(path).getroot()
    t=root.find('.//transpose')
    trans=int(t.findtext('chromatic'))+12*int(t.findtext('octave-change','0'))
    notes=[]
    previous=None
    for bar in root.findall('.//part/measure'):
        duration=sum(int(n.findtext('duration')) for n in bar.findall('note'))
        beats=root.findtext('.//time/beats'); unit=root.findtext('.//time/beat-type')
        assert duration==int(beats)*16//int(unit) or bar.get('implicit')=='yes', (path,bar.get('number'))
        for n in bar.findall('note'):
            p=n.find('pitch')
            pitch=None if p is None else 12*(int(p.findtext('octave'))+1)+PC[p.findtext('step')]+int(p.findtext('alter','0'))
            if pitch is not None:
                assert 58<=pitch<=90,(path,pitch)
            ties=[tie.get('type') for tie in n.findall('tie')]
            if 'stop' in ties:
                assert previous and 'start' in previous[2] and previous[0]==pitch,(path,bar.get('number'))
            elif previous:
                assert 'start' not in previous[2], (path,bar.get('number'))
            notes.append((pitch,int(n.findtext('duration')),ties))
            previous=notes[-1]
    assert 'start' not in previous[2]
    return [(None if p is None else p+trans,d,t) for p,d,t in notes],root

catalog=json.loads((SITE/'catalog.json').read_text())
pages=0
for piece in catalog['pieces']:
    soprano,_=events(SITE/piece['variants']['soprano']['musicxml'])
    for instrument,variant in piece['variants'].items():
        seq,root=events(SITE/variant['musicxml'])
        assert len(seq)==len(soprano)
        expected=catalog['instruments'][instrument]
        assert root.findtext('.//instrument-name')==expected['english']
        assert root.findtext('.//midi-program')==str(expected['program'])
        for baseline,note in zip(soprano,seq):
            assert baseline[1:]==note[1:]
            if baseline[0] is None:
                assert note[0] is None
            else:
                assert note[0]==baseline[0]+12*variant['soundingOctaveOffset'],(piece['id'],instrument,baseline,note)
        pdf=PdfReader(SITE/variant['pdf'])
        assert len(pdf.pages)==len(variant['pages'])
        assert piece['title'] in pdf.metadata.title
        for page in pdf.pages:
            assert abs(float(page.mediabox.width)-A4[0])<.1
            assert abs(float(page.mediabox.height)-A4[1])<.1
            assert len(page.images)==0
        for page in variant['pages']:
            assert (SITE/page['image']).is_file()
        pages+=len(pdf.pages)
        print(piece['id'],instrument,len(pdf.pages),'A4 vector pages / transpose, rhythm, ties OK')
print(f'PASS: {len(catalog["pieces"])} pieces, 24 editions, {pages} pages')

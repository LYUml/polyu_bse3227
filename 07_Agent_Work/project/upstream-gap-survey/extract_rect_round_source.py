"""Crosscheck visually read protected source cells against native PDF words."""
import fitz,json,hashlib
from pathlib import Path
P=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work')
source=P/'project/full-network-transition-study/ashrae2021.pdf'
words=fitz.open(source)[21].get_text('words')
headers=sorted([w for w in words if 355<w[0]<374 and 120<w[1]<590 and w[4] in ['1','2','5','10','20','50']],key=lambda w:w[1])
matrix=[]
for i,w in enumerate(headers):
    end=headers[i+1][1] if i+1<len(headers) else 590
    rows=[]
    for ld in [1,3]:
        anchor=[v for v in words if 378<v[0]<392 and w[1]-.6<=v[1]<end-.6 and v[4]==str(ld)]
        assert len(anchor)==1
        cells=sorted([x for x in words if 395<x[0]<530 and abs(x[1]-anchor[0][1])<.6],key=lambda x:x[0])
        assert len(cells)==6
        rows.append([float(x[4]) for x in cells])
    matrix.append(rows)
expected=[[[.27,.27,.28,.29,.31,.37],[.27,.27,.28,.29,.30,.33]],
    [[.25,.25,.26,.27,.29,.35],[.25,.25,.25,.26,.28,.33]],
    [[.18,.18,.19,.20,.22,.28],[.18,.18,.19,.20,.22,.27]],
    [[.11,.11,.12,.13,.15,.21],[.11,.11,.12,.13,.14,.19]],
    [[.04,.04,.05,.06,.08,.14],[.04,.04,.05,.06,.07,.12]],
    [[0,0,.01,.02,.04,.10],[0,0,.01,.02,.04,.09]]]
assert matrix==expected
out=dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),Re_axis=[1,2,5,10,20,50],
    L_over_D_axis=[1,3],B_axis=[.1,1,5,10,20,50],coefficients=matrix,
    locator='Printed21Fitting4-6/printed22right-hand contraction table,L/D1and3rows',
    manual_visual_transcription_matches_native_text=True)
target=P/'runs/rect-round-source-study/right-L1-L3.json';assert not target.exists()
target.write_text(json.dumps(out,indent=2))
print('72protected source cells:visual/native-text crosscheckpass')

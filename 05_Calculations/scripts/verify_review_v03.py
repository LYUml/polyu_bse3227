"""Read-only native DWG audit plus shared-data reconciliation."""
import csv,json
from cad_native import ROOT,CACHE,run,sha
dwg=ROOT/'03_Design_Drawings/BSE3227_HVAC_Review_v03.dwg'
out=CACHE/'v03_native_counts.txt'
expr=[f'(setq f (open "{out.as_posix()}" "w"))','(write-line (itoa (getvar "INSUNITS")) f)']
layers={'M-SUP-DIFF':160,'M-VAV':20,'M-FLEX':80,'M-DUCT':50,'M-DUCT-TEXT':49}
for layer in layers:
    expr.append(f'(write-line (itoa (sslength (ssget "_X" \'((8 . "{layer}") (410 . "Model"))))) f)')
expr.append('(close f)')
run(dwg,expr,'verify_v03')
counts=list(map(int,out.read_text().split()))
assert counts==[4,*layers.values()],counts
data=ROOT/'05_Calculations/data'
def read(n):return list(csv.DictReader((data/n).open()))
diff=read('diffusers_v03.csv');vav=read('vav_boxes_v03.csv');duct=read('ducts_v03.csv')
for v in vav:
    children=[r for r in diff if r['vav']==v['id']]
    assert len(children)==4
    assert abs(sum(float(r['max_lps']) for r in children)-float(v['max_lps']))<1e-6
for d in duct:
    children=d['downstream_vavs'].split(';')
    assert abs(sum(float(v['max_lps']) for v in vav if v['id'] in children)-float(d['flow_lps']))<1e-6
    assert float(d['velocity_ms']) <= (10 if d['kind']=='main' else 8)
    assert float(d['friction_Pa_m'])<=.8 and float(d['aspect_ratio'])<=4
manifest=json.loads((data/'source_manifest.json').read_text())
assert all(sha(ROOT/r['path'])==r['sha256'] for r in manifest)
result={'drawing':str(dwg.relative_to(ROOT)),'sha256':sha(dwg),'units_mm':counts[0]==4,
        'native_layer_counts':dict(zip(layers,counts[1:])),
        'interpretation':'160 diffuser polylines represent 80 symbols; 50 duct entities comprise 49 sections and AHU outline.',
        'flow_conservation':True,'rigid_velocity_friction_aspect':True,'original_source_hashes_unchanged':True,
        'visual_review':'A1 PDF rendered and inspected; all 49 section IDs and schedule rows visible. Upper-zone label crowding remains for final issue.',
        'release_status':'Course-method ADPI calculated separately; final report and annotation coordination outstanding.'}
(data/'native_review_v03.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))

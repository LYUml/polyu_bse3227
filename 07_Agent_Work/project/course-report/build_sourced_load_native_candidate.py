"""Reuse preserved-entity native revision and existing VAV sheet authoring."""
from pathlib import Path
import csv,json,os,hashlib,math
import ezdxf
from bsa.duct_schedule import run as schedule_run
from bsa.drawing_revision import run as revise
from bsa.vav_schedule import author,rows_from
from bsa.duct_sheet_native import run as native_sheet
from bsa.native_cad import DEFAULT_EXE
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');P=B/'07_Agent_Work';R=P/'runs/course-sourced-load-candidate'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
old=list(csv.DictReader((B/'05_Calculations/Connection Layout Duct Sizing.csv').open()));oldby={r['Section']:r for r in old}
project=read(R/'ducts.json')
for section in project['sections']:
    before=oldby[section['id']];section['candidates']=[c for c in section['candidates'] if c['width_m']<=float(before['Width mm'])/1000+1e-10 and c['height_m']<=float(before['Height mm'])/1000+1e-10]
    assert section['candidates']
project['basis']+='; additional design choice: neither width nor height may exceed the current source section, preserving the existing nominal route corridor'
(R/'ducts-corridor.json').write_text(json.dumps(project,indent=2));schedule=schedule_run(R/'ducts-corridor.json',R/'schedule-corridor',allocation_path=R/'allocation.json',allocation_sha256=sha(R/'allocation.json'))
assert all(not r['failures'] for r in schedule['sections'])
rows=list(csv.DictReader((R/'schedule-corridor/schedule.csv').open()));by={r['Section']:r for r in rows}
dxf=P/'runs/course-diffuser-native-final/reopened/source-export.dxf';doc=ezdxf.readfile(dxf);texts=[e for e in doc.modelspace().query('TEXT') if e.dxf.layer=='BSA_SCHEDULE'];edits=[]
def edit(entity,value):
    if entity.dxf.text==value:return
    edits.append(dict(handle=entity.dxf.handle,expected=dict(layer=entity.dxf.layer,text=entity.dxf.text,insert=[entity.dxf.insert.x,entity.dxf.insert.y]),replacement=dict(text=value,insert=[entity.dxf.insert.x,entity.dxf.insert.y])))
for ident,row in by.items():
    tag=next(e for e in texts if e.dxf.text==ident);cells=sorted([e for e in texts if abs(e.dxf.insert.y-tag.dxf.insert.y)<1e-8],key=lambda e:e.dxf.insert.x)
    assert len(cells)==5
    values=[ident,f"{float(row['Flow L/s']):.1f}",f"{float(row['Width mm']):.0f} x {float(row['Height mm']):.0f}",f"{float(row['Velocity m/s']):.2f}",f"{float(row['Friction Pa/m']):.3f}"]
    for entity,value in zip(cells,values):edit(entity,value)
note=doc.entitydb['8EFE'];assert note.dxf.layer=='BSA_NOTES';edit(note,'Model1400:600x600mm,6in;150W/m2 assumed. AHU/VAV sizes and ports pending.')
source=B/'03_Design_Drawings/Connection_Layout/Supply Air Distribution.dwg';recipe=R/'native-revision.json';sheet=read(P/'project/bse3227-flow-direction-inputs/native.json')['sheet']
data=dict(schema='bsa.drawing-revision/1',source='Source-backed150W/m2 unadopted coursework candidate; same80positions/20groups/47routes, finite corridor-preserving sizing and prescribed1400family.',drawing=os.path.relpath(source,recipe.parent).replace('\\','/'),drawing_sha256=sha(source),edits=edits,sheet=sheet)
recipe.write_text(json.dumps(data,indent=2));native=revise(recipe,R/'native',autocad=DEFAULT_EXE)
allocation=read(R/'allocation.json');terms={t['id']:t for t in allocation['terminals']};centres=read(P/'runs/course-refined-report-inputs/vav-centres.json')
groups=list(csv.DictReader((B/'05_Calculations/Connection_Layout/VAV Connection Schedule.csv').open()));review=dict(groups=[])
for group in groups:
    ids=group['Diffuser outlets'].split(', ');review['groups'].append(dict(id=group['VAV'],outlet_count=4,maximum_flow_L_s=sum(terms[k]['maximum_flow_L_s'] for k in ids),routes=[dict(terminal=k,plan_length_m=math.dist(terms[k]['center_m'],centres[group['VAV']])) for k in ids]))
vav=rows_from(review,allocation);V=R/'vav';V.mkdir(exist_ok=False);source=V/'VAV Connection Schedule.dxf';labels,reference=author(vav,source)
settings=dict(source_sha256=sha(source),layers=['BSA_VAV_TABLE'],sheet=dict(source='Source-inherited candidate flow schedule;100mmprint reference',window_drawing_units=[0,0,290,200],scale_denominator=1,reference_handle=reference,pdf_tolerance_mm=.2))
(V/'native-settings.json').write_text(json.dumps(settings,indent=2));vav_native=native_sheet(source,V/'native-settings.json',V/'native',DEFAULT_EXE);(V/'rows.json').write_text(json.dumps(vav,indent=2));(V/'review.json').write_text(json.dumps(vav_native,indent=2))
summary=read(R/'review.json');summary.update(native_DWG_candidate='Saved/reopened,all intended TEXT revisions compared;actual plot review pending',native_main_review=native,native_vav_review=vav_native,all47_dimensions_nonincreasing=True,actual_changed_duct_sizes=sum((float(r['Width mm']),float(r['Height mm']))!=(float(oldby[r['Section']]['Width mm']),float(oldby[r['Section']]['Height mm'])) for r in rows))
(R/'review-native.json').write_text(json.dumps(summary,indent=2));print(json.dumps(dict(native_main=native['native_reopen_pass'],native_vav=vav_native['native_reopen_pass'],edits=len(edits),changed_duct_sizes=summary['actual_changed_duct_sizes'])))

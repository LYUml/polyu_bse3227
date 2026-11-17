"""Compose existing native-plan review/table engines for the recentered scenario."""
import csv
import hashlib
import json
import math
from pathlib import Path
import ezdxf
from bsa import vav_recenter as parent,vav_schedule as table,air_terminal_drawing as connections
from bsa.duct_sheet_native import run as native_run,compare

ROOT=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227')
WORK=ROOT/'07_Agent_Work'
SOURCE=WORK/'runs/vav-recenter-friction-compensated'
OUT=WORK/'runs/recentered-vav-connection-schedule'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if OUT.exists():raise ValueError('Fresh output required')
assert parent.verify(SOURCE)['integrity_pass']
revision=json.loads((SOURCE/'revision.json').read_text())
workflow=Path(revision['workflow'])
allocation=workflow/'air-allocation/allocation.json'
project=SOURCE/'inputs/ducts.json';binding=SOURCE/'inputs/binding.json'
drawing=SOURCE/'delivery/native/reopened/source-export.dxf'
policy=json.loads(Path(revision['policy']).read_text());layers=policy['layers']
pins={str(p):sha(p) for p in [SOURCE/'revision.json',drawing,allocation,project,binding,
    Path(__file__),Path(parent.__file__),Path(table.__file__),Path(connections.__file__)]}
OUT.mkdir()
review=connections.run(drawing,allocation,project,binding,OUT/'connections.json',layers=layers)
allocated=json.loads(allocation.read_text());rows=table.rows_from(review,allocated)
assert len(rows)==20 and sum(r['outlet_count'] for r in rows)==80
original=parent.resolve(Path(revision['plan']),workflow,revision['native_task'])
old_review=connections.inspect(ezdxf.readfile(original['source']),allocated,json.loads(original['project'].read_text())['tree'],json.loads(original['binding'].read_text()),layers)
old_rows={r['id']:r for r in table.rows_from(old_review,allocated)}
changes=[]
for row in rows:
    old=old_rows[row['id']]
    for key in ['terminals','maximum_flow_L_s','minimum_flow_L_s','outlet_count']:assert row[key]==old[key]
    expected=next((x for x in revision['geometry']['changes'] if x['id']==row['id']),None)
    if expected:
        assert row['maximum_plan_length_m']<old['maximum_plan_length_m']
        changes.append(dict(id=row['id'],old_maximum_plan_m=old['maximum_plan_length_m'],new_maximum_plan_m=row['maximum_plan_length_m']))
    else:assert row==old
assert len(changes)==10
dxf=OUT/'VAV Connection Schedule.dxf'
labels,reference=table.author(rows,dxf)
with (OUT/'VAV Connection Schedule.csv').open('w',newline='',encoding='utf-8') as f:
    writer=csv.writer(f);writer.writerow(table.HEADERS);writer.writerows(table.cells(r) for r in rows)
settings=dict(source_sha256=sha(dxf),layers=['BSA_VAV_TABLE'],sheet=dict(
    source='Recentered saved-native scenario table; generated100mm print reference, not building geometry scale',
    window_drawing_units=[0,0,290,200],scale_denominator=1,reference_handle=reference,pdf_tolerance_mm=.2))
(OUT/'native-settings.json').write_text(json.dumps(settings,indent=2))
native=native_run(dxf,OUT/'native-settings.json',OUT/'native','C:/Program Files/Autodesk/AutoCAD 2027/accoreconsole.exe')
assert native['native_reopen_pass']
compare(dxf,OUT/'native/reopened/source-export.dxf',['BSA_VAV_TABLE'])
assert parent.verify(SOURCE)['integrity_pass']
assert all(sha(Path(p))==h for p,h in pins.items())
record=dict(source_recenter_revision_sha256=sha(SOURCE/'revision.json'),groups=20,terminals=80,
    unchanged_terminal_membership=True,unchanged_maximum_minimum_flows=True,changed_plan_length_groups=changes,
    maximum_flow_L_s=math.fsum(r['maximum_flow_L_s'] for r in rows),minimum_flow_L_s=math.fsum(r['minimum_flow_L_s'] for r in rows),
    native_reopen_pass=True,visual_review='pending',rows=rows,labels=labels,inputs=pins,
    scope=table.SCOPE,design_accepted=False)
(OUT/'review.json').write_text(json.dumps(record,indent=2))
print(json.dumps({k:v for k,v in record.items() if k not in ['rows','labels','inputs','changed_plan_length_groups']},indent=2))

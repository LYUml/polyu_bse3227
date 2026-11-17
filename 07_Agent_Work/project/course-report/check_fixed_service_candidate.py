"""Reuse fixed service cells and native conditions; change geometry, never loads."""
import csv,json,hashlib,math
from pathlib import Path
from shapely.geometry import shape,Point

B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227')
R=B/'07_Agent_Work/runs/course-diffuser-fixed-service-checked';R.mkdir(exist_ok=False)
source=B/'07_Agent_Work/runs/course-diffuser-position-screen/axis1_-0.15.json'
candidate=json.loads(source.read_text());baseline=B/'07_Agent_Work/runs/vav-recenter-design-reviewed/delivery/allocation/allocation.json'
allocation=json.loads(baseline.read_text());terms={t['id']:t for t in allocation['terminals']}
original=B/'05_Calculations/Connection_Layout/Native K-Select Ratio Check.csv'
rows=list(csv.DictReader(original.open(encoding='utf-8-sig')))
lengths={(r['terminal'],r['direction']):r['screened_length_m'] for r in candidate['cases']}
changes={r['id']:r['center_m'] for r in candidate['changes']}
assert all(shape(terms[k]['geometry']).covers(Point(xy)) for k,xy in changes.items())
for row in rows:
    row['previous_L_m']=row['L_m'];row['previous_native_ratio']=row['native_ratio']
    row['L_m']=lengths[row['terminal'],row['direction']]
    row['native_ratio']=float(row['native_T025_m'])/row['L_m']
    row['classroom_interval_met']=1<=row['native_ratio']<=3.4
assert len(rows)==640 and all(r['classroom_interval_met'] for r in rows)
with (R/'Native K-Select Candidate Ratios.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
result=dict(scope='150mm southward source-row relocation within unchanged explicit service cells. Same flows and same49 native K-Select conditions; geometric ratio comparison, not ADPI prediction.',
    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),baseline_sha256=hashlib.sha256(baseline.read_bytes()).hexdigest(),
    native_source_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),moved_terminals=len(changes),
    all_moved_centres_inside_original_service_cells=True,flows_unchanged=True,ratio_checks=640,
    baseline_ratio_range=[min(float(r['previous_native_ratio']) for r in rows),max(float(r['previous_native_ratio']) for r in rows)],
    candidate_ratio_range=[min(r['native_ratio'] for r in rows),max(r['native_ratio'] for r in rows)],
    critical_maximum=max(rows,key=lambda r:r['native_ratio']),critical_minimum=min(rows,key=lambda r:r['native_ratio']),
    changes=changes,selected=False,ADPI_verified=False,
    pending=['Exact flex and source obstruction checks','Guarded native drawing updates/reopen/plot','Report and schedules consistency'])
(R/'review.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k not in ['critical_maximum','critical_minimum','changes']},indent=2))

"""Independent raw-native group/line/cell reconciliation and clean delivery."""
import csv
import hashlib
import json
import math
from pathlib import Path
import shutil
import ezdxf

ROOT=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227')
AGENT=Path('C:/Users/lyuml-win/Desktop/building-services-agent')
RUN=ROOT/'07_Agent_Work/runs/recentered-vav-connection-schedule'
r=json.loads((RUN/'review.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert all(sha(Path(p))==h for p,h in r['inputs'].items())
allocation=next(Path(p) for p in r['inputs'] if Path(p).as_posix().endswith('air-allocation/allocation.json'))
allocated={x['id']:x for x in json.loads(allocation.read_text())['terminals']}
plan=next(Path(p) for p in r['inputs'] if Path(p).as_posix().endswith('reopened/source-export.dxf'))
doc=ezdxf.readfile(plan);assert doc.units==4
metres=lambda xyz:tuple(float(v)*.001 for v in xyz)
table=ezdxf.readfile(RUN/'native/reopened/source-export.dxf');assert table.units==4
texts=list(table.modelspace().query('TEXT'))
edges=[8,32,120,154,188,220,252,280]
csv_rows=list(csv.reader((RUN/'VAV Connection Schedule.csv').open(encoding='utf-8')))
seen=set();cells=0;lengths=[]
for index,row in enumerate(r['rows']):
    circle=doc.entitydb[next(g['vav_handle'] for g in json.loads((RUN/'connections.json').read_text())['groups'] if g['id']==row['id'])]
    start=metres(circle.dxf.center);distances=[];maxflows=[];minflows=[]
    for route in row['routes']:
        tid=route['terminal'];assert tid not in seen;seen.add(tid)
        source=allocated[tid];end=tuple(source['center_m'])+(0.,)
        line=doc.entitydb[route['flex_handle']];assert line.dxftype()=='LINE'
        ends=[metres(line.dxf.start),metres(line.dxf.end)]
        assert (math.dist(ends[0],start)<1e-8 and math.dist(ends[1],end)<1e-8) or (math.dist(ends[1],start)<1e-8 and math.dist(ends[0],end)<1e-8)
        polygon=doc.entitydb[route['terminal_handle']]
        points=list(polygon.get_points());centre=(sum(p[0] for p in points)*.001/4,sum(p[1] for p in points)*.001/4,0.)
        assert math.dist(centre,end)<1e-8
        length=math.dist(*ends);assert math.isclose(length,route['plan_length_m'],rel_tol=1e-12)
        distances.append(length);lengths.append(length)
        maxflows.append(source['maximum_flow_L_s']);minflows.append(source['minimum_flow_L_s'])
    expected=[row['id'],', '.join(row['terminals']),f'{math.fsum(maxflows):.1f}',f'{math.fsum(minflows):.1f}',f'{min(distances):.3f}',f'{max(distances):.3f}',str(len(distances))]
    assert csv_rows[index+1]==expected
    for col,value in enumerate(expected):
        matches=[e for e in texts if math.dist(tuple(e.dxf.insert),(edges[col]+1.5,158-(index+1)*6-4.1,0))<1e-7]
        assert len(matches)==1 and matches[0].dxf.text==value
        cells+=1
assert seen==set(allocated) and cells==140 and len(lengths)==80
native=json.loads((RUN/'native/native-sheet.json').read_text());assert native['native_reopen_pass'] and native['plot']['pdf_reference_pass']
assert sha(RUN/'native/Supply Air Distribution.pdf')==native['plot']['pdf_sha256']
summary=dict(vav_groups=20,terminal_count=80,raw_native_flex_lengths_reconciled=80,native_cells_reconciled=140,
    csv_cells_reconciled=140,changed_group_plan_lengths=10,unchanged_flows_and_membership=True,
    maximum_flow_L_s=r['maximum_flow_L_s'],minimum_flow_L_s=r['minimum_flow_L_s'],
    total_plan_flex_m=math.fsum(lengths),maximum_plan_flex_m=max(lengths),
    native_DWG_reopen_pass=True,native_entity_count=native['generated_geometry']['generated_entity_count'],
    actual_PDF_page_visually_inspected=True,plot_reference_expected_mm=100.,plot_reference_measured_mm=native['plot']['reference_measured_mm'],
    installed_flex_lengths_verified=False,hardware_selected=False,full_pressure_verified=False,ADPI_verified=False,design_accepted=False,
    source_revision_sha256=r['source_recenter_revision_sha256'],scope='Recentered Connection_Layout schedule only; earlier network study remains a separate scenario')
dest=ROOT/'03_Design_Drawings/Connection_Layout'
for source,name in [(RUN/'native/Supply Air Distribution.dwg','VAV Connection Schedule.dwg'),(RUN/'native/Supply Air Distribution.pdf','VAV Connection Schedule.pdf')]:
    target=dest/name;assert not target.exists();shutil.copyfile(source,target)
calc=ROOT/'05_Calculations/Connection_Layout';calc.mkdir(exist_ok=True)
csv_target=calc/'VAV Connection Schedule.csv';assert not csv_target.exists();shutil.copyfile(RUN/'VAV Connection Schedule.csv',csv_target)
summary['deliverable_sha256']={str(p.relative_to(ROOT)):sha(p) for p in [dest/'VAV Connection Schedule.dwg',dest/'VAV Connection Schedule.pdf',csv_target]}
(RUN/'independent-review.json').write_text(json.dumps(summary,indent=2))
(ROOT/'05_Calculations/Connection_Layout/Schedule_Check.json').write_text(json.dumps(summary,indent=2))
(AGENT/'docs/evidence/recentered-vav-schedule.json').write_text(json.dumps(summary,indent=2))
scope=dest/'Review scope.md'
with scope.open('a',encoding='utf-8') as f:f.write('\n\nThe matching VAV Connection Schedule now uses this same recentered native\nlayout:20groups/80terminals,10updatedgroupconnectionlengths,unchanged prescribed\nmaximum/minimum flows and membership. Saved/reopened DWG185entities,140native\ncells and80rawplanconnections independently reconcile. Actual A4PDF inspected;\n100mmreference measured100.033667mm. Companion CSV/check are under\n05_Calculations/Connection_Layout. These are straight XY lower-bound lengths,\nnot installed flex lengths or selected hardware. Full pressure and ADPI remain\nunresolved; do not combine with the separate earlier network-study geometry.\n')
print(json.dumps(summary,indent=2))

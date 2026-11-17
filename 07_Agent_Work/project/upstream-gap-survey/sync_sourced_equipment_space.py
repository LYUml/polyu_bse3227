"""Move source-dimensioned candidate casings to actual saved inlet boundaries."""
import copy,csv,hashlib,json
from pathlib import Path
import numpy as np
import ifcopenshell
from ifcopenshell.util import placement
from bsa.obstacle_boxes import append

BASE=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs');RUN=BASE/'sourced-inlet-network'
SOURCE=RUN/'Supply Network.ifc';OLD=BASE/'vav-finite-placement/placement.json'
LOCAL=BASE/'rect-round-sourced-design/analytic-inlet-assemblies/author-review.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads(OLD.read_text());local=json.loads(LOCAL.read_text())
model=ifcopenshell.open(str(SOURCE));oldpoints={r['id']:np.array(r['node_m']) for r in old['placements']}
cases={r['id']:r for r in local['cases']};points={};deltas={};rows=[];coordinates=[]
flows=json.loads((RUN/'flow-review.json').read_text())
for name,case in cases.items():
    port=model.by_guid(case['round_ports']['outlet']['guid']);frame=placement.get_local_placement(port.ObjectPlacement)
    points[name]=frame[:3,3];deltas[name]=points[name]-oldpoints[name]
    assert np.allclose(points[name],case['length_budget']['proposed_inlet_point_m'],atol=1e-9,rtol=0)
    qmax=flows['cases']['maximum']['port_flows'][port.GlobalId]['flow_m3_s']*1000
    qmin=flows['cases']['minimum']['port_flows'][port.GlobalId]['flow_m3_s']*1000
    coordinates.append(dict(id=name,inlet_point_m=points[name].tolist(),shift_m=deltas[name].tolist(),
        qmax_L_s=qmax,qmin_L_s=qmin,nominal_diameter_mm=case['diameter_m']*1000,
        source_port_guid=port.GlobalId,datum='Proposed equipment inlet collar entrance; installation unverified'))
for original in old['obstacles']:
    row=copy.deepcopy(original);name=row['properties']['VAVID'];case=cases[name]
    row['origin_m']=(np.array(row['origin_m'])+deltas[name]).tolist()
    row['properties'].update(SourceIntegratedIFCSHA256=sha(SOURCE),
        DatumAssumption='Actual saved round outlet is proposed equipment inlet collar entrance; no installed product datum acceptance')
    row['source']+='; placement reconciled to current saved circular outlet'
    if row['id'].endswith('INLET-RESERVATION'):
        obj=model.by_guid(case['round_guid']);profile=obj.Representation.Representations[0].Items[0].SweptArea
        frame=placement.get_local_placement(obj.ObjectPlacement);axis=int(np.argmax(abs(frame[:3,2])))
        for k in range(3):
            if k==axis:continue
            change=2*profile.Radius-row['size_m'][k]
            assert change>0 and abs(change-2*profile.WallThickness)<1e-9
            row['origin_m'][k]-=change/2;row['size_m'][k]=2*profile.Radius
        row['properties']['SpaceBasis']='Actual saved outside diameter, excluding unverified insulation/clearance'
    rows.append(row)
assert sum(np.linalg.norm(d)>1e-8 for d in deltas.values())==8 and len(rows)==80
report=append(SOURCE,rows,{OLD,LOCAL,Path(__file__)},RUN/'equipment-space',
    prefix='VAV_CANDIDATE_',pset_name='BSA_VAVCandidate',
    metadata=dict(GeometryScope='Actual129body inlet network plus source-dimensioned casing and reservation proxies'),body_context_id=10)
assert report['original_entities_unchanged']
for row in rows:
    if not row['id'].endswith('CASING'):continue
    name=row['properties']['VAVID'];case=cases[name]
    frame=np.array(case['frame']);z=frame[:3,2]
    expected=points[name]+z*(3.375*.0254+15.5*.0254/2)
    assert np.allclose(np.array(row['origin_m'])+np.array(row['size_m'])/2,expected,atol=1e-8,rtol=0)
check=dict(source_ifc_sha256=sha(SOURCE),combined_ifc_sha256=report['saved_ifc_sha256'],
    original129network_records_unchanged=True,casing_count=20,reservation_count=60,
    moved_casings=8,all20casings_match_current_inlet_datum=True,
    inlet_reservations_use_saved_outside_diameter=True,rows=coordinates,
    discharge_plenum_or_flex_origins_verified=False,installed_clearance_verified=False,design_accepted=False)
(RUN/'equipment-space/sync-review.json').write_text(json.dumps(check,indent=2))
with (RUN/'equipment-space/VAV Inlet Coordinates.csv').open('w',newline='',encoding='utf8') as f:
    w=csv.writer(f);w.writerow(['VAV','Inlet X m','Inlet Y m','Inlet Z m assumed','Nominal bore mm','Maximum L/s','Minimum L/s','Shift X m','Shift Y m','Shift Z m'])
    for row in coordinates:w.writerow([row['id'],*row['inlet_point_m'],row['nominal_diameter_mm'],row['qmax_L_s'],row['qmin_L_s'],*row['shift_m']])
print(json.dumps(dict(casings=20,moved=8,source_network_unchanged=True,installed_clearance_verified=False)))

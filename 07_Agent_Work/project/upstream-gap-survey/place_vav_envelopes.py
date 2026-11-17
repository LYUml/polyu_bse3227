"""Finite candidate casing and reserved installation spaces, not installed units."""
import hashlib,json
from pathlib import Path
import numpy as np
from bsa.obstacle_boxes import append

ROOT=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227')
BASE=ROOT/'07_Agent_Work/runs'
SOURCE=BASE/'recentered-network-integrated/Supply Network.ifc'
INLETS=BASE/'vav-manufacturer-capacity/inlet-revision.json'
NODES=BASE/'recentered-vav-connection-schedule/revised-junction.json'
OUT=BASE/'vav-finite-placement'
assert not OUT.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
design=json.loads(INLETS.read_text())
nodes={n['node']:n for n in json.loads(NODES.read_text())['nodes']}
rows=[];placements=[]
for row in design['rows']:
    node=nodes[row['id']];assert len(node['incidents'])==1
    inc=node['incidents'][0];assert inc['role']=='incoming'
    point=np.array(node['point_m'])
    axis=-np.array(inc['outward_unit_vector']);trans=np.array([-axis[1],axis[0],0.])
    assert np.count_nonzero(axis)==1 and axis[2]==0
    # NEW design datum: existing abstract node = inlet collar entrance centre.
    # Existing rigid duct remains unchanged, so the round lead is only a required
    # replacement-space reservation; it is never asserted physically connected.
    A=3.375*.0254;L=row['casing_length_m'];W=row['casing_width_m'];H=row['casing_height_m']
    common=dict(VAVID=row['id'],NominalInlet_in=row['revised_candidate_size_in'],
        SourceNodeSHA256=sha(NODES),CandidateSHA256=sha(INLETS),
        ElevationBasis='Inherited study centreline z=0; not installed elevation',
        DatumAssumption='Original abstract VAV node is proposed inlet collar entrance; not a source-specified equipment datum',
        PhysicalEquipmentSelected=False)
    def box(suffix,along,across,z,kind,source):
        points=[point+axis*a+trans*t+np.array([0.,0.,h]) for a in along for t in across for h in z]
        p=np.array(points);lo=p.min(axis=0);hi=p.max(axis=0)
        item=dict(id=row['id']+'-'+suffix,origin_m=lo.tolist(),size_m=(hi-lo).tolist(),
            source=source,properties={**common,'RepresentationKind':kind})
        rows.append(item);return item
    body=box('CASING',[A,A+L],[-W/2,W/2],[-H/2,H/2],'Manufacturer casing envelope; not internal product geometry',
        'LMHS MiniCatalog printed A2-7; manufacturer dimensions, candidate placement assumption')
    D=row['revised_candidate_size_in']*.0254
    lead=box('INLET-RESERVATION',[-3*D,0],[-D/2,D/2],[-D/2,D/2],
        'Reserved straight circular duct space; box is not a duct solid',
        'SDIOM PDF6 Step2A recommends3D; nominal round size from candidate')
    # Reserve both sides while control handedness is unselected. The 6.25in
    # projection is diagrammed A2-7; full casing-length coverage is conservative
    # host design policy, not claimed exact control-enclosure geometry.
    for sign,label in [(-1,'LEFT'),(1,'RIGHT')]:
        across=sorted([sign*W/2,sign*(W/2+6.25*.0254+.4572)])
        box('ACCESS-'+label,[0,A+L],across,[-H/2,H/2],
            'Both-side conservative control/access reservation; not physical equipment',
            'SDIOM PDF3 recommends18in access; A2-7 control projection6.25in; length/height and both-side extent host design policy')
    placements.append(dict(id=row['id'],node_m=point.tolist(),airflow_axis=axis.tolist(),
        inlet_straight_space_m=3*D,casing_source_section=inc['section'],
        previous_rectangular_section_m=[inc['width_m'],inc['height_m']],
        new_round_inlet_nominal_m=D,connection_complete=False))
assert len(rows)==80
report=append(SOURCE,rows,{INLETS,NODES,Path(__file__)},OUT,
    prefix='VAV_CANDIDATE_',pset_name='BSA_VAVCandidate',
    metadata=dict(GeometryScope='Casing and reservation boxes, not connected MEP or acceptance'),body_context_id=10)
report['placements']=placements
report['scope']='Actual saved finite candidate placement; source network unchanged, no new ports, ducts or equipment accepted'
(OUT/'placement.json').write_text(json.dumps(report,indent=2))
print(json.dumps(dict(boxes=len(rows),original_entities_unchanged=report['original_entities_unchanged'],
    native_checks=report['calculated_checks_pass'],connected_equipment=False),indent=2))

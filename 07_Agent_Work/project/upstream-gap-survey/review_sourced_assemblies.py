"""Saved round leads, exact source flows and actual local connections."""
import hashlib,json,math
from pathlib import Path
import numpy as np
import ifcopenshell,ifcopenshell.geom as geom
from ifcopenshell.util import placement,system
from fluids.friction import friction_factor
from bsa.circular_geometry import configure
from bsa.solid_clash import from_mesh
from bsa.clash import run as clash

BASE=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs')
RUN=BASE/'rect-round-sourced-design/analytic-inlet-assemblies'
report=json.loads((RUN/'author-review.json').read_text())
native=json.loads((RUN/'independent-review.json').read_text())
IFC=RUN/'VAV Inlet Assemblies.ifc';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(IFC)==report['ifc_sha256']==native['ifc_sha256']
common=json.loads((RUN.parent/'kernel-common-validated/kernel-review.json').read_text())
assert len(common['results'])==20 and all(r['STEP_reimport_units_pass'] for r in common['results'])
model=ifcopenshell.open(str(IFC))
assert len(model.by_type('IfcDuctFitting'))==20 and len(model.by_type('IfcDuctSegment'))==20 and len(model.by_type('IfcDistributionPort'))==80
actual={tuple(sorted((r.RelatingPort.GlobalId,r.RelatedPort.GlobalId))) for r in model.by_type('IfcRelConnectsPorts')}
expected={tuple(sorted((r['ports']['circle']['guid'],r['round_ports']['inlet']['guid']))) for r in report['cases']}
assert actual==expected and len(actual)==20
air_path=BASE/'vav-recenter-friction-compensated/inputs/ducts.json'
air=json.loads(air_path.read_text())['air']
rho,mu,rough=[air[k] for k in ['density_kg_m3','viscosity_Pa_s','roughness_m']]
nodes={n['node']:n for n in json.loads((BASE/'recentered-vav-connection-schedule/revised-junction.json').read_text())['nodes']}
settings=geom.settings();settings.set(settings.USE_WORLD_COORDS,True);configure(settings)
rows=[]
for row in report['cases']:
    obj=model.by_guid(row['round_guid']);solid=obj.Representation.Representations[0].Items[0]
    profile=solid.SweptArea;D=2*(profile.Radius-profile.WallThickness);L=solid.Depth
    assert math.isclose(D,row['diameter_m'],abs_tol=1e-12) and math.isclose(L,3*D,abs_tol=1e-12)
    assert np.allclose(placement.get_local_placement(obj.ObjectPlacement),row['round_frame'],atol=1e-9,rtol=0)
    ports={p.Name:p for p in system.get_ports(obj)};assert set(ports)=={'inlet','outlet'}
    for name,port in ports.items():
        assert port.GlobalId==row['round_ports'][name]['guid']
        assert np.allclose(placement.get_local_placement(port.ObjectPlacement),row['round_ports'][name]['frame'],atol=1e-9,rtol=0)
    face_a=placement.get_local_placement(model.by_guid(row['ports']['circle']['guid']).ObjectPlacement)
    face_b=placement.get_local_placement(ports['inlet'].ObjectPlacement)
    assert np.allclose(face_a[:3,3],face_b[:3,3],atol=1e-9,rtol=0) and np.allclose(face_a[:3,2],-face_b[:3,2],atol=1e-9,rtol=0)
    assert np.allclose(placement.get_local_placement(ports['outlet'].ObjectPlacement)[:3,3],row['length_budget']['proposed_inlet_point_m'],atol=1e-9,rtol=0)
    shape=geom.create_shape(settings,obj);v=np.array(shape.geometry.verts).reshape(-1,3);f=np.array(shape.geometry.faces).reshape(-1,3)
    volume=from_mesh((v,f)).volume();expected_volume=math.pi*(profile.Radius**2-(D/2)**2)*L
    assert math.isclose(volume,expected_volume,rel_tol=.001)
    calculations={};qmax=nodes[row['id']]['incidents'][0]['flow_L_s']/1000
    for condition,fraction in [('maximum',1),('minimum',.4)]:
        Q=qmax*fraction;velocity=Q/(math.pi*D**2/4);Re=rho*velocity*D/mu
        assert Re>4000
        factor=friction_factor(Re=Re,eD=rough/D)
        calculations[condition]=dict(flow_m3_s=Q,velocity_m_s=velocity,Re=Re,Darcy_factor=factor,
            straight_friction_Pa=factor*L/D*rho*velocity**2/2,complete_local_pressure_Pa=None)
    assert calculations['maximum']['velocity_m_s']<=8
    rows.append(dict(id=row['id'],saved_diameter_m=D,saved_round_length_m=L,native_wall_valid=True,
        joint_frames_coincident_opposed=True,source_boundary_matches_proposed_point=True,
        material_interface_basis='Exact matching analytic nominal inner radius and0.8mm outer section offset; product collar/seal remains unverified',calculations=calculations))
policy=BASE/'reduced-branch-network-reviewed/raw-clash-policy.json'
raw=clash(IFC,policy,RUN/'raw-clash')
assert raw['valid_geometry_count']==40 and raw['intersection_pair_count']==0
assert raw['clearance_violation_pair_count']==20 and not raw['accepted_contacts']
result=dict(ifc_sha256=sha(IFC),air_input_sha256=sha(air_path),air=air,
    native_transition_cases=20,native_round_leads=20,owned_ports=80,actual_local_links=20,
    native_all40geometries_valid=True,raw_intersection_pairs=0,raw_clearance_pairs=20,contact_waivers=0,
    common_worker_direct_geometry_source_verified=True,common_worker_STEP_units_reimport_pass=True,
    rows=rows,network_merged=False,full_pressure_verified=False,design_accepted=False,
    pending=['Existing rectangular source duct replacements','Equipment collar/seal interfaces','Actual equipment positions and architecture',
        'Transition and joint losses; static/total pressure stations','Controls, acoustics and discharge distribution'])
(RUN/'assembly-review.json').write_text(json.dumps(result,indent=2))
print(json.dumps(dict(bodies=40,ports=80,links=20,raw_intersections=0,unwaived_clearances=20,
    maximum_round_friction_range_Pa=[min(r['calculations']['maximum']['straight_friction_Pa'] for r in rows),max(r['calculations']['maximum']['straight_friction_Pa'] for r in rows)])))

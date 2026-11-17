from pathlib import Path
import json,math,itertools
import numpy as np,ifcopenshell,ifcopenshell.geom
from ifcopenshell.util.placement import get_local_placement
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs');P=B/'j-outlet-reducer-candidate-verified';m=ifcopenshell.open(str(P/'Candidate Round Reducers.ifc'));x=json.loads((P/'review.json').read_text());ids={r['product_guid'] for r in x['records']};bounds={};settings=ifcopenshell.geom.settings();settings.set(settings.USE_WORLD_COORDS,True)
for e in m.by_type('IfcElement'):
 if not e.Representation:continue
 if not (e.is_a('IfcDistributionElement') or e.Name.endswith('CASING') or e.Name.startswith('CANDIDATE_VAV-')):continue
 if e.GlobalId in ids:
  f=get_local_placement(e.ObjectPlacement);radius=.254/2+.0008;L=x['design_dimensions']['total_m'];pts=np.array([(r,z,t) for r,z,t in itertools.product([-radius,radius],[0,L],[-radius,radius])]);v=pts@f[:3,:3].T+f[:3,3]
 else:
  shape=ifcopenshell.geom.create_shape(settings,e);v=np.array(shape.geometry.verts).reshape(-1,3)
 bounds[e.GlobalId]=(v.min(axis=0),v.max(axis=0),e.Name)
assert len(bounds)==249
candidates=[]
for a,b in itertools.combinations(bounds,2):
 if a not in ids and b not in ids:continue
 al,ah,an=bounds[a];bl,bh,bn=bounds[b]
 if np.all(np.minimum(ah,bh)-np.maximum(al,bl)>2e-5):candidates.append([an,bn])
review=dict(physical_scope_bodies=249,reducers=80,excluded_nonphysical_reservations=60,reducer_AABB_overlap_pairs=candidates,scope='Conservative full upstream-diameter cylinder boxes for reducer vs existing physical scope and each other; previous169body solid check retained',no_reducer_intersection_proven_by_disjoint_bounds=not candidates,installation_clearance_verified=False,design_accepted=False);(P/'bounds-review.json').write_text(json.dumps(review,indent=2));print(review)
R=B/'j-outlet-8in-routed-plan-reviewed';routes=json.loads((R/'review.json').read_text());envelope=[]
for r in routes['routes']:
 rad=r['radius_m'];base=r['plan_centreline_m'];full=r['total_plan_including_reducer_m'];envelope.append(dict(terminal=r['terminal'],minimum_drop_for_quarter_turn_m=rad,minimum_flex_path_at_drop_equal_R_m=base+(math.pi/2-1)*rad,maximum_drop_for_4m_flex_geometric_budget_m=4-base+(2-math.pi/2)*rad,minimum_all_component_path_including_rigid_reducer_m=full+(math.pi/2-1)*rad))
review=dict(assumed_final_vertical_turn='Quarter circle with same1.5D radius replacing last R metres of horizontal tangent, followed by vertical straight; not actual installation',flex_only_4m_budget_is_not_regulatory_acceptance=True,minimum_possible_drop_m=.3048,smallest_maximum_drop_budget_m=min(e['maximum_drop_for_4m_flex_geometric_budget_m'] for e in envelope),actual_drop_unknown=True,records=envelope,design_accepted=False);(R/'vertical-envelope.json').write_text(json.dumps(review,indent=2));print({k:v for k,v in review.items() if k!='records'})

"""Source-dimensioned J outlet candidate; no final product/route acceptance."""
import json,hashlib,itertools,math
from pathlib import Path
import numpy as np,ifcopenshell,ezdxf
from ifcopenshell.util.placement import get_local_placement
from bsa.obstacle_boxes import append
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs');R=B/'sourced-inlet-network';O=B/'j-outlet-candidate';O.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=R/'equipment-space/model.ifc';m=ifcopenshell.open(str(source));s=json.loads((R/'equipment-space/sync-review.json').read_text());groups=json.loads((B/'recentered-vav-connection-schedule/connections.json').read_text())['groups'];g={x['id']:x for x in groups}
dxf=B/'vav-recenter-friction-compensated/delivery/native/reopened/source-export.dxf';d=ezdxf.readfile(dxf);assert d.units==4
rows=[];records=[];inch=.0254
for r in s['rows']:
 frame=get_local_placement(m.by_guid(r['source_port_guid']).ObjectPlacement);z=frame[:3,2];side=np.cross([0,0,1],z);assert abs(z[2])<1e-9 and np.count_nonzero(abs(z)>1e-9)==1
 nominal=round(r['nominal_diameter_mm']/25.4);assert nominal in [12,14]
 W,H=([16,15] if nominal==12 else [20,17.5]);W*=inch;H*=inch
 start=np.array(r['inlet_point_m'])+z*((3.375+15.5)*inch);end=start+z*36*inch
 corners=[p+side*x+np.array([0,0,h]) for p in [start,end] for x in [-W/2,W/2] for h in [-H/2,H/2]]
 lo=np.min(corners,axis=0);hi=np.max(corners,axis=0)
 rows.append(dict(id=r['id']+'-J-PLENUM',origin_m=lo.tolist(),size_m=(hi-lo).tolist(),source='LMHS MiniCatalog printed A2-10/A2-11 J four-outlet attenuator; candidate envelope, datum assumption',properties=dict(VAVID=r['id'],OutletType='J',NominalInlet_in=nominal,PhysicalEquipmentSelected=False,RepresentationKind='Solid coordination envelope, not airflow volume or fabricated wall')))
 ports=[dict(id=f'{r["id"]}-J-{i+1}',point_m=(end-z*a*inch+side*sign*(W/2+3.375*inch)).tolist(),direction=(side*sign).tolist()) for i,(a,sign) in enumerate(itertools.product([6.375,20.375],[-1,1]))]
 targets=[]
 for route in g[r['id']]['routes']:
  e=d.entitydb[route['terminal_handle']];assert e.dxftype()=='LWPOLYLINE' and e.closed;pts=np.array(list(e.get_points()))[:,:2]*.001;centre=(pts.min(axis=0)+pts.max(axis=0))/2
  targets.append(dict(id=route['terminal'],point_m=[*centre,0.]))
 def lengths(order):return [math.dist(ports[i]['point_m'],targets[j]['point_m']) for i,j in enumerate(order)]
 order=min(itertools.permutations(range(4)),key=lambda p:(max(lengths(p)),sum(lengths(p))))
 routes=[dict(outlet=ports[i]['id'],terminal=targets[j]['id'],terminal_point_m=targets[j]['point_m'],plan_lower_bound_m=lengths(order)[i]) for i,j in enumerate(order)]
 records.append(dict(id=r['id'],inlet_size_in=nominal,ports=ports,routes=routes,maximum_plan_lower_bound_m=max(lengths(order)),outlet_bore_m=9.875*inch,maximum_outlet_velocity_if_equal_split_m_s=r['qmax_L_s']/1000/4/(math.pi*(9.875*inch)**2/4),assignment='All24permutations checked; minimize longest planar distance, then total; same20groups/80terminals preserved',physical_product_selected=False))
report=append(source,rows,{dxf,B/'vav-manufacturer-capacity/LMHS_MiniCatalog.pdf',Path(__file__)},O/'geometry',prefix='CANDIDATE_',pset_name='BSA_JOutletCandidate',metadata=dict(Scope='20candidateJplenum envelopes appended to previous209model; no installed clearance or full pressure acceptance'),body_context_id=10)
proof=dict(source_ifc_sha256=sha(source),catalogue_sha256=sha(B/'vav-manufacturer-capacity/LMHS_MiniCatalog.pdf'),source_locator='Printed A2-10/A2-11; visually reviewed 4-outlet side/end views and J table row',dimensions_in=dict(plenum_length=36,outlet_collar_projection=3.375,outlet_bore=9.875,X=6.375,Y=14),datum_assumptions='Base discharge at inlet collar entrance+3.375+15.5in; plenum starts at base discharge, slip-drive overlap not inferred; outlet centre at casing midheight; z=0 inherited reference',candidate_count=20,outlets=80,terminal_count=80,maximum_plan_lower_bound_m=max(x['maximum_plan_lower_bound_m'] for x in records),original209records_unchanged=report['original_entities_unchanged'],records=records,installed_length_verified=False,pressure_verified=False,design_accepted=False)
(O/'review.json').write_text(json.dumps(proof,indent=2));print(json.dumps({k:v for k,v in proof.items() if k not in ['records','datum_assumptions']}))

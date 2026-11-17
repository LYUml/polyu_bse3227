"""Finite-radius outlet departure paths, separate from installed flex design."""
from pathlib import Path
import json,math,hashlib
import numpy as np,ezdxf
from scipy.optimize import brentq
from fluids.friction import friction_factor
from bsa.duct_sheet_native import run as native
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs');X=B/'j-outlet-candidate';O=B/'j-outlet-8in-routed-plan-labelled';O.mkdir(exist_ok=False)
source=X/'review.json';x=json.loads(source.read_text());rev=json.loads((B/'vav-recenter-friction-compensated/revision.json').read_text());allocation=Path(rev['workflow'])/'air-allocation/allocation.json';a=json.loads(allocation.read_text());terms={r['id']:r for r in a['terminals']};air=json.loads((B/'sourced-inlet-network/pressure-units-reviewed/maximum/analysis.json').read_text())['air'];print('air',air)
reducer_path=B/'j-outlet-reducer-candidate-verified/review.json';reducer=json.loads(reducer_path.read_text());ends={r['plenum_outlet_id']:r['new_branch_origin_m'] for r in reducer['records']}
for group in x['records']:
 for port in group['ports']:port['point_m']=ends[port['id']]
D=8*.0254;R=1.5*D;lead=.15;routes=[]
for g in x['records']:
 ports={p['id']:p for p in g['ports']};q=0
 for old in g['routes']:
  p=ports[old['outlet']];P=np.array(p['point_m'])[:2];T=np.array(old['terminal_point_m'])[:2];u=np.array(p['direction'])[:2];n=np.array([-u[1],u[0]]);v=T-P;sgn=1 if v@n>=0 else -1;n*=sgn;A=P+lead*u;v=T-A;parallel=float(v@u);transverse=float(v@n);assert parallel>R and transverse>0
  theta=brentq(lambda t:-parallel*math.sin(t)+(transverse-R)*math.cos(t)+R,0,math.pi/2,xtol=1e-14)
  E=A+R*math.sin(theta)*u+R*(1-math.cos(theta))*n;C=A+R*n;tangent=math.cos(theta)*u+math.sin(theta)*n;L=float((T-E)@tangent)
  assert L>0 and np.linalg.norm(E+L*tangent-T)<1e-10 and abs(np.linalg.norm(E-C)-R)<1e-10
  terminal=terms[old['terminal']];assert np.allclose(terminal['center_m'],T,atol=1e-10,rtol=0);q+=terminal['maximum_flow_L_s']
  pressure={}
  for condition in ['maximum','minimum']:
   Q=terminal[condition+'_flow_L_s']/1000;velocity=Q/(math.pi*D**2/4);Re=air['density_kg_m3']*velocity*D/air['viscosity_Pa_s'];f=friction_factor(Re=Re,eD=air['roughness_m']/D)
   pressure[condition]=dict(flow_m3_s=Q,Reynolds=Re,Darcy_f=f,straight_only_Pa=f*(lead+L)/D*air['density_kg_m3']*velocity**2/2,arc_fitting_loss_Pa=None,total_pressure_Pa=None)
  routes.append(dict(vav=g['id'],terminal=old['terminal'],outlet=p['id'],P=P.tolist(),A=A.tolist(),E=E.tolist(),T=T.tolist(),centre=C.tolist(),turn_deg=math.degrees(theta),signed_bulge=sgn*math.tan(theta/4),reducer_total_length_m=reducer['design_dimensions']['total_m'],radius_m=R,initial_straight_m=lead,final_straight_m=L,arc_length_m=R*theta,plan_centreline_m=lead+R*theta+L,total_plan_including_reducer_m=reducer['design_dimensions']['total_m']+lead+R*theta+L,bore_m=D,pressure=pressure))
 assert abs(q-next(r for r in json.loads((B/'sourced-inlet-network/equipment-space/sync-review.json').read_text())['rows'] if r['id']==g['id'])['qmax_L_s'])<1e-8
assert len(routes)==80 and len({r['terminal'] for r in routes})==80
points=np.array([r[k] for r in routes for k in ['P','A','E','T']]);lo=points.min(axis=0);hi=points.max(axis=0);scale=200;offset=np.array([2.,6.])-lo
assert np.all(hi-lo<[54,27])
d=ezdxf.new('R2018');d.units=6;m=d.modelspace()
for layer,color in [('OUTLET_PATH',5),('TERMINAL',3),('VAV',7),('NOTES',7)]:d.layers.new(layer,dxfattribs={'color':color})
for r in routes:
 p,a,e,t=[np.array(r[k])+offset for k in ['P','A','E','T']]
 m.add_lwpolyline([(p[0],p[1],0),(a[0],a[1],r['signed_bulge']),(e[0],e[1],0),(t[0],t[1],0)],format='xyb',dxfattribs={'layer':'OUTLET_PATH'})
 m.add_circle(t,.15,dxfattribs={'layer':'TERMINAL'})
for g in x['records']:
 p=np.mean([r['point_m'][:2] for r in g['ports']],axis=0)+offset;m.add_text(g['id'],dxfattribs={'height':.28,'insert':p+[-.6,0.],'layer':'VAV'})
for txt,y,size in [('EIGHT INCH BRANCH CONNECTION STUDY',38.2,.8),('80 nominal8in branches after reducers | assumed plan z=0 | 1:200',36.5,.48),('Design targets: R=1.5D, initial straight150mm; not product bend data',35,.43),('Terminal vertical turns, transitions, flex product and installation remain unresolved',2,.4),('Straight friction only; all bend/adapter/plenum/equipment losses remain unknown',.7,.4)]:m.add_text(txt,dxfattribs={'height':size,'insert':(2,y),'layer':'NOTES'})
ref=m.add_line((2,4.8),(12,4.8),dxfattribs={'layer':'NOTES'});m.add_text('10m reference',dxfattribs={'height':.4,'insert':(12.7,4.6),'layer':'NOTES'})
p=O/'Four Outlet Connection Routes.dxf';d.saveas(p)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
settings=dict(source_sha256=sha(p),layers=['OUTLET_PATH','TERMINAL','VAV','NOTES'],sheet=dict(source='Source-bound80terminal plan, candidate outlet departure tangency; not installed flex geometry',window_drawing_units=[0,0,58,40],scale_denominator=scale,reference_handle=ref.dxf.handle,pdf_tolerance_mm=.3));(O/'settings.json').write_text(json.dumps(settings,indent=2))
review=dict(inputs={str(p):sha(p) for p in [source,allocation,reducer_path,Path(__file__)]},route_count=80,distinct_terminals=80,source_group_flows_reconciled=True,assumptions=dict(bore_m=D,radius_over_bore=1.5,initial_straight_m=lead,elevation_m=0,roughness_m=air['roughness_m']),maximum_plan_including_reducer_m=max(r['total_plan_including_reducer_m'] for r in routes),maximum_plan_centreline_m=max(r['plan_centreline_m'] for r in routes),turn_range_deg=[min(r['turn_deg'] for r in routes),max(r['turn_deg'] for r in routes)],routes=routes,pressure_budget_complete=False,installed_length_verified=False,design_accepted=False)
(O/'review.json').write_text(json.dumps(review,indent=2));n=native(p,O/'settings.json',O/'native','C:/Program Files/Autodesk/AutoCAD 2027/accoreconsole.exe');print(json.dumps(dict(routes=80,max_plan_m=review['maximum_plan_centreline_m'],turn_range_deg=review['turn_range_deg'],native_reopen=n['native_reopen_pass'])))



from pathlib import Path
import json,time,hashlib,importlib.metadata
import numpy as np
from scipy.optimize import differential_evolution
from shapely.geometry import shape,mapping
from bsa.air_allocation import prepare
from bsa.manufacturer_adpi import catalogue,lengths,screen
from bsa.terminal_performance import calculate
P=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');B=P/'07_Agent_Work/runs';out=B/'manufacturer-adpi-spatial-refinement';out.mkdir(exist_ok=False)
base=json.loads((B/'manufacturer-adpi-comparison/comparison.json').read_text())
plan=json.loads(Path(base['plan']).read_text());task=next(t for t in plan['tasks'] if t['kind']=='air_allocation')
source=Path(base['plan']).parent/task['project'];spec=json.loads(source.read_text());boundary_file=(source.parent/spec['boundary']).resolve()
assert hashlib.sha256(boundary_file.read_bytes()).hexdigest()==spec['boundary_sha256']
geo=json.loads(boundary_file.read_text());boundary=shape(geo);tables=catalogue(Path(base['performance_pdf']))
curves=json.loads((B/'manufacturer-adpi-native-curves/curves.json').read_text())
bounds_json=json.loads((B/'manufacturer-adpi-wall-neck-diagnosis/same-length-necessary-bound.json').read_text())
ratio_bounds=np.array([bounds_json['ratio_bounds'][c] for c in ['maximum','minimum']])
xmin,ymin,xmax,ymax=boundary.bounds;splitx=95.209266;splity=36.595584
best=None;calls=0;start=time.monotonic();policy={'parameter_names':['main_left_inward_shift_m','main_join_shift_m','bay_left_inward_shift_m','right_inward_shift_m','bottom_inward_shift_m','main_top_inward_shift_m','bay_bottom_shift_m','bay_top_inward_shift_m','hypothetical_downward_distance_m'],'bounds':[[0,3.5],[-2,2],[0,3],[-3,0],[0,3.5],[-3,0],[-1,2],[-3,0],[0,3]],'finite_budget':{'maxiter':35,'popsize':5,'seed':3227,'polish':False},'scope':'Separate80terminal two-zone row/column candidate; actual source boundary and full fresh nearest-centre area allocation each evaluation. Hypothetical downward travel only on aligned opposing jets. Necessary ratio envelope objective; exact source screen required after search. No actual building height claimed.'}
(out/'search-policy.json').write_text(json.dumps(policy,indent=2))
original=base['scenarios'][0]['terminals']
def points(v):
 a,b,c,d,e,f,g,h,drop=v
 xs=sorted(set(t['center_m'][0] for t in original));ys=sorted(set(t['center_m'][1] for t in original))
 pts=[]
 for t in original:
  x,y=t['center_m'];u=(x-xs[0])/(xs[7]-xs[0]) if x<95 else (x-xs[8])/(xs[-1]-xs[8])
  xx=x+(a*(1-u)+b*u if x<95 else c*(1-u)+d*u)
  z=(y-ys[0])/(ys[5]-ys[0]) if y<36.595584 else (y-ys[6])/(ys[7]-ys[6])
  yy=y+(e*(1-z)+f*z if y<36.595584 else g*(1-z)+h*z)
  pts.append({'id':t['id'],'center_m':[float(xx),float(yy)]})
 return pts
def evaluate(v,save=False):
 global best,calls
 calls+=1
 if time.monotonic()-start>170:raise TimeoutError('Declared170second evaluation budget exhausted')
 try:
  pts=points(v);allocation=prepare(geo,pts,spec['load_inputs'],spec['turndown']);Ls=lengths(boundary,pts)
 except ValueError:return 1e5
 pos=np.array([t['center_m'] for t in pts]);allL=np.array([[Ls[t['id']][k] for k in ['east','west','north','south']] for t in pts]);opposing=np.zeros((80,4),dtype=bool)
 for j,(dx,dy) in enumerate([(1,0),(-1,0),(0,1),(0,-1)]):
  dv=pos[None,:,:]-pos[:,None,:];along=dv[:,:,0]*dx+dv[:,:,1]*dy;perp=dv[:,:,0]*dy-dv[:,:,1]*dx
  ds=np.where((along>1e-8)&(abs(perp)<1e-8),along/2,np.inf).min(axis=1)
  opposing[:,j]=abs(ds-allL[:,j])<1e-8
 effective=allL+opposing*v[-1]
 q=np.array([[t['maximum_flow_L_s'],t['minimum_flow_L_s']] for t in allocation['terminals']])
 costs=[];throws=[]
 for neck,table in tables.items():
  qs=np.array([r['flow_L_s'] for r in table]);ts=np.array([r['T025_m'] for r in table])
  T=np.interp(q,qs,ts);ratio=T[:,:,None]/effective[:,None,:]
  low=ratio_bounds[:,0][None,:,None];high=ratio_bounds[:,1][None,:,None]
  cost=(np.maximum(low/ratio-1,0)**2+np.maximum(ratio/high-1,0)**2).sum(axis=(1,2))
  cost+=100*((q<qs[0])|(q>qs[-1])).sum(axis=1)
  costs.append(cost);throws.append(T)
 costs=np.array(costs).T;chosen=costs.argmin(axis=1);local=costs.min(axis=1);score=float((local>1e-14).sum()+.01*local.sum()+.01*local.max())
 if best is None or score<best['score']:
  best={'score':score,'parameters':[float(x) for x in v],'calls':calls,'elapsed_seconds':time.monotonic()-start,'necessary_envelope_failing_terminals':int((local>1e-15).sum()),'maximum_terminal_penalty':float(local.max())}
  (out/'best-progress.json').write_text(json.dumps(best,indent=2))
 if save:
  failures=[];selection=[]
  for i,t in enumerate(allocation['terminals']):
   neck=list(tables)[chosen[i]];table=tables[neck]
   selection.append({'terminal':t['id'],'neck_inch':int(neck),'effective_lengths_m':effective[i].tolist(),'opposing_directions':opposing[i].tolist()})
   for ci,(cond,loads) in enumerate([('maximum',[40,60]),('minimum',[20,40])]):
    perf=calculate(table,float(q[i,ci]))
    if perf['status']!='within_catalogue':failures.append({'terminal':t['id'],'condition':cond,'reason':'outside_catalogue'});continue
    for di,name in enumerate(['east','west','north','south']):
     for load in loads:
      reading=screen(curves,load,perf['T025_m']/effective[i,di])
      if reading['status']!='paired_curve_threshold_met':failures.append({'terminal':t['id'],'condition':cond,'direction':name,'load_Btuh_ft2':load,**reading})
  (out/'allocation.json').write_text(json.dumps(allocation,indent=2))
  (out/'candidate.json').write_text(json.dumps({'parameters':[float(x) for x in v],'terminals':pts,'selection':selection,'failures':failures,'whole_exact_source_screen_pass':not failures,'scope':policy['scope'],'design_accepted':False,'objective':'Failed-terminal count first, then small ratio penalty; fresh allocations and unchanged source limits'},indent=2))
 return score
try:
 initial=[0,0,0,0,0,0,0,0,2.32]
 baseline_score=evaluate(initial)
 (out/'baseline.json').write_text(json.dumps({'parameters':initial,'score':baseline_score,'necessary_failures':best['necessary_envelope_failing_terminals']}))
 result=differential_evolution(evaluate,policy['bounds'],x0=initial,maxiter=35,popsize=5,rng=np.random.default_rng(3227),polish=False,updating='immediate')
 terminal='finite search completed';message=str(result.message)
except TimeoutError as exc:terminal='declared time limit reached';message=str(exc)
assert best is not None
# Saved best re-evaluation is permitted outside search time budget; source calculations unchanged.
start=time.monotonic();evaluate(best['parameters'],save=True)
summary={'search_state':terminal,'message':message,'best':best,'versions':{n:importlib.metadata.version(n) for n in ['scipy','numpy','shapely','fluids']},'source_boundary_sha256':spec['boundary_sha256'],'curve_sha256':curves['source_pdf_sha256'],'scope':policy['scope'],'design_accepted':False,'objective':'Failed-terminal count first, then small ratio penalty; fresh allocations and unchanged source limits'}
(out/'search-result.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary),flush=True)

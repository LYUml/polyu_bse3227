from pathlib import Path
from decimal import Decimal
import json,re,hashlib,csv,math
import numpy as np
from bsa.openfoam_transient import read_samples,difference,window_statistics
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/openfoam-pressure-verification');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();cases={};series={}
q=json.loads((B/'plenum-family-1-transient-kepsilon-pilot/pilot-inputs.json').read_text())['flow_m3_s']
for kind in ('baseline','extended'):
 c=B/('plenum-family-1-boundary-comparison-'+kind);run=json.loads((c/'native-run-review.json').read_text());assert run['returncode']==0 and run['end_U_exists'];policy=json.loads((c/'comparison-policy.json').read_text());src=B/policy['source_case'];assert all(sha(src/p)==h for p,h in policy['source_sha256'].items())
 expected=[Decimal(str(policy['start_s']))+Decimal('.00025')*i for i in range(1,int((Decimal('.5')-Decimal(str(policy['start_s'])))/Decimal('.00025'))+1)]
 log=(c/'foamRun.log').read_text();assert [Decimal(t) for t in re.findall(r'^Time = ([0-9.eE+-]+)s',log,re.M)]==expected
 hashes={}
 def read(name,column):
  fs=list((c/'postProcessing'/name).rglob('surfaceFieldValue.dat'));assert len(fs)==1;hashes[name]=sha(fs[0]);a=read_samples(fs[0].read_text(),column,delta_t_s='.00025');assert [t for t,_ in a]==[Decimal(str(policy['start_s']))]+expected;return a
 flux_checks={}
 for name,target in q.items():
  a=read('flux_'+name,'sum(phi)');target=-target if name=='inlet' else target;error=max(abs(v-target)/abs(target) for _,v in a);assert error<1e-10;flux_checks[name]={'samples':len(a),'maximum_relative_error':error}
 inlet=read('pressure_inlet','average(Pt)');paths={};series[kind]={}
 for i in range(4):
  name='outlet_'+str(i);out=read('pressure_'+name,'average(Pt)') if kind=='baseline' else read('original_pressure_'+str(i),'average(Ptf)')
  if kind=='extended':
   f=read('original_flux_'+str(i),'orientedSum(phi)');error=max(abs(v-q[name])/q[name] for _,v in f);assert error<1e-7;flux_checks['original_'+name]={'samples':len(f),'maximum_relative_error':error}
  d=difference(inlet,out);series[kind][name]=d;previous=window_statistics(d,'.40','.45');last=window_statistics(d,'.45','.50');paths[name]={'previous_window':previous,'comparison_window':last,'mean_drift_Pa':last['time_weighted_mean']-previous['time_weighted_mean']}
 fields={}
 for n in ('U','p','k','epsilon','nut'):
  f=c/'0.5'/n;t=f.read_text();m=re.search(r'internalField\s+nonuniform\s+List<(scalar|vector)>\s+(\d+)\s*\((.*?)\n\)\s*;',t,re.S);assert m and int(m[2])==(142480 if kind=='baseline' else 190880)
  a=np.fromstring(m[3].replace('(',' ').replace(')',' '),sep=' ');assert np.isfinite(a).all()
  if n in ('k','epsilon','nut'):assert a.min()>=0
  fields[n]={'cells':int(m[2]),'sha256':sha(f)}
 cases[kind]={'run':run,'histories_sha256':hashes,'flux_checks':flux_checks,'final_fields':fields,'path_pressure_diagnostics':paths,'maximum_Courant':max(float(v) for v in re.findall(r'Courant Number mean: [^\s]+ max: ([^\s]+)',log))}
comparison={}
for name in series['baseline']:
 b=cases['baseline']['path_pressure_diagnostics'][name]['comparison_window']['time_weighted_mean'];e=cases['extended']['path_pressure_diagnostics'][name]['comparison_window']['time_weighted_mean'];comparison[name]={'baseline_mean_Pa':b,'extended_original_station_mean_Pa':e,'difference_Pa':e-b,'relative_difference_baseline_reference':(e-b)/abs(b) if b else None}
r={'scope':'Same-original-station prescribed-flow outlet extension diagnostic; not validated fitting losses','window_s':[.45,.50],'cases':cases,'comparison':comparison,'stationarity_accepted':False,'domain_independence_accepted':False,'time_mesh_independence_accepted':False,'physical_inlet_wall_validation_accepted':False,'pressure_adopted':False};out=B/'paired-boundary-comparison';out.mkdir(exist_ok=True);(out/'review.json').write_text(json.dumps(r,indent=2)+'\n')
with (out/'Boundary Comparison History.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['case','path','time_s','pressure_difference_Pa'])
 for kind,paths in series.items():
  for name,rows in paths.items():w.writerows((kind,name,str(t),v) for t,v in rows)
print(json.dumps(comparison))

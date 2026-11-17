from pathlib import Path
import json,re,hashlib,math,csv
from decimal import Decimal
import numpy as np
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/openfoam-pressure-verification');c=B/'plenum-family-1-initialized-residence'
receipt=json.loads((c/'native-run-review.json').read_text());assert receipt['returncode']==0 and receipt['final_U_exists']
policy=json.loads((c/'residence-policy.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=B/'plenum-family-1-potential-outlet-reference';assert all(sha(source/p)==h for p,h in policy['source_inputs_sha256'].items())
log=(c/'foamRun.log').read_text();times=[Decimal(x) for x in re.findall(r'^Time = ([0-9.eE+-]+)s',log,re.M)];expected=[Decimal('.005')+Decimal('.00025')*i for i in range(1,981)];assert times==expected
hist_times=[Decimal('.005')]+expected
q=json.loads((B/'plenum-family-1-transient-kepsilon-pilot/pilot-inputs.json').read_text())['flow_m3_s']
def history(n):
 fs=list((c/'postProcessing'/n).rglob('surfaceFieldValue.dat'));assert len(fs)==1
 rows=[l.split() for l in fs[0].read_text().splitlines() if l.strip() and not l.startswith('#')];assert len(rows)==981 and [Decimal(x[0]) for x in rows]==hist_times
 a=np.array([float(x[1]) for x in rows]);assert np.isfinite(a).all();return a
flux={};pressures={}
for n,target in q.items():
 a=history('flux_'+n);target=-target if n=='inlet' else target;err=float(np.max(np.abs(a-target))/abs(target));assert err<1e-10
 flux[n]={'samples':len(a),'maximum_relative_error':err};pressures[n]=history('pressure_'+n)
fields={}
for n in ('U','p','k','epsilon','nut'):
 path=c/'0.25'/n;t=path.read_text();m=re.search(r'internalField\s+nonuniform\s+List<(scalar|vector)>\s+(\d+)\s*\((.*?)\n\)\s*;',t,re.S);assert m and int(m[2])==142480
 a=np.fromstring(m[3].replace('(',' ').replace(')',' '),sep=' ');assert np.isfinite(a).all()
 if n in ('k','epsilon','nut'):assert a.min()>=0
 fields[n]={'cells':142480,'component_min':float(a.min()),'component_max':float(a.max()),'sha256':sha(path)}
x=np.array([float(t) for t in hist_times]);windows={};diffs={n:pressures['inlet']-p for n,p in pressures.items() if n!='inlet'}
for n,d in diffs.items():
 w=[]
 for lo,hi in ((.15,.20),(.20,.25)):
  sel=(x>=lo)&(x<=hi);xx=x[sel];y=d[sel];assert len(y)==201
  mean=float(np.trapezoid(y,xx)/(hi-lo));rms=float(np.sqrt(np.trapezoid((y-mean)**2,xx)/(hi-lo)))
  w.append({'from_s':lo,'to_s':hi,'samples_including_both_endpoints':len(y),'time_weighted_mean_Pa':mean,'time_weighted_rms_Pa':rms,'range_Pa':float(np.ptp(y))})
 windows[n]={'windows':w,'mean_change_Pa':w[1]['time_weighted_mean_Pa']-w[0]['time_weighted_mean_Pa'],'stationary_statistics_accepted':False}
with (c/'Residence Pressure History.csv').open('w',newline='') as f:
 writer=csv.writer(f);writer.writerow(['time_s']+list(diffs));writer.writerows(zip(x,*diffs.values()))
r={'scope':'One-reference-residence transient evolution; not validated design pressure','run':receipt,'physical_times_match980steps':True,'history_samples_including_restart':981,'flow_checks':flux,'final_fields':fields,'physical_end_s':.25,'nominal_residence_s':policy['reference_residence_s'],'nominal_residence_fraction':.25/policy['reference_residence_s'],'pressure_window_diagnostics':windows,'maximum_Courant':max(float(v) for v in re.findall(r'Courant Number mean: [^\s]+ max: ([^\s]+)',log)),'mesh_independence_accepted':False,'temporal_independence_accepted':False,'near_wall_physics_accepted':False,'stationary_statistics_accepted':False,'pressure_adopted':False,'design_accepted':False}
(c/'residence-review.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))

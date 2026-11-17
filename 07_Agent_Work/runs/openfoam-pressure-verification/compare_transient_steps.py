from pathlib import Path
import re,json,math,hashlib
from decimal import Decimal
import numpy as np
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/openfoam-pressure-verification')
a=B/'plenum-family-1-transient-kepsilon-pilot';b=B/'plenum-family-1-transient-kepsilon-halfstep'
def values(p):
 t=p.read_text();m=re.search(r'internalField\s+nonuniform\s+List<(\w+)>\s+(\d+)\s*\(',t);assert m
 closing=re.search(r'\n\)\s*;',t[m.end():]);assert closing
 end=m.end()+closing.start();data=np.fromstring(t[m.end():end].replace('(',' ').replace(')',' '),sep=' ')
 count=int(m[2]);data=data.reshape((count,3)) if m[1]=='vector' else data
 assert count==142480 and np.isfinite(data).all()
 return data
fields={}
for name in ['U','p','k','epsilon','nut']:
 x=values(a/'0.005'/name);y=values(b/'0.005'/name);diff=y-x
 if name in ['k','epsilon','nut']:assert min(x.min(),y.min())>=0
 fields[name]={'native_cells':142480,'coarse_min':float(x.min()),'coarse_max':float(x.max()),'fine_min':float(y.min()),'fine_max':float(y.max()),'relative_L2_change_fine_reference':float(np.linalg.norm(diff)/np.linalg.norm(y)),'maximum_absolute_component_change':float(abs(diff).max())}
log=(b/'foamRun.log').read_text();ts=[Decimal(x) for x in re.findall(r'^Time = ([0-9.eE+-]+)s\s*$',log,re.M)]
assert ts==[Decimal('.000125')*i for i in range(1,41)]
policy=json.loads((a/'pilot-inputs.json').read_text());fluxes={}
for name,q in policy['flow_m3_s'].items():
 f=list((b/'postProcessing'/('flux_'+name)).rglob('surfaceFieldValue.dat'));assert len(f)==1
 rows=[r.split() for r in f[0].read_text().splitlines() if r.strip() and not r.startswith('#')];assert len(rows)==41 and Decimal(rows[0][0])==0
 initial=rows[0];assert float(initial[1])==0
 advanced=rows[1:]
 assert [Decimal(r[0]) for r in advanced]==ts
 target=-q if name=='inlet' else q;vs=[float(r[1]) for r in advanced]
 assert all(math.isclose(v,target,rel_tol=1e-12) for v in vs)
 fluxes[name]={'native_samples_preserved':41,'initial_unadvanced_time0_flux_m3_s':float(initial[1]),'advanced_samples':40,'maximum_relative_error':max(abs(v-target)/abs(target) for v in vs)}
yp=list((b/'postProcessing/wall_yPlus').rglob('yPlus.dat'));assert len(yp)==1
last=[r.split() for r in yp[0].read_text().splitlines() if r.strip() and not r.startswith('#')][-1]
courants=[float(x) for x in re.findall(r'Courant Number mean: [^\s]+ max: ([^\s]+)',log)]
r={'scope':'Same physical0.005s startup comparison, not statistically developed pressure','coarse_deltaT_s':.00025,'fine_deltaT_s':.000125,'same_end_time_s':.005,'only_solver_input_change':'deltaT halved; output writeInterval doubled to retain same physical final write','mesh_initial_fields_model_schemes_BCs_preserved':True,'fine_time_labels_exact':True,'fine_native_returncode':json.loads((b/'native-run-review.json').read_text())['returncode'],'fields':fields,'five_port_flux_checks':fluxes,'fine_maximum_reported_Courant':max(courants),'fine_final_native_yPlus':dict(zip(['minimum','maximum','average'],map(float,last[2:]))),'interpretation':'Two early-time step sizes quantify startup sensitivity only; not convergence order, temporal independence, stationary statistics or physical validation','pressure_adopted':False,'design_accepted':False}
(b/'same-time-comparison.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r))

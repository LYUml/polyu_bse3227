from pathlib import Path
import json,os,subprocess,hashlib,re,itertools,math
from decimal import Decimal
P=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/openfoam-pressure-verification');c=P/'plenum-family-1-transient-kepsilon-pilot'
policy=json.loads((c/'pilot-inputs.json').read_text());names=['U','p','k','epsilon','nut','phi'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before={n:sha(c/'0.005'/n) for n in names}
text='FoamFile {format ascii;class dictionary;object functions;}\n'
for name in policy['flow_m3_s']:
 text+='flux_'+name+' {type surfaceFieldValue;libs ("libfieldFunctionObjects.dll");regionType patch;name air_'+name+';operation sum;fields (phi);writeFields false;writeControl timeStep;writeInterval 1;}\n'
text+='wall_yPlus {type yPlus;libs ("libfieldFunctionObjects.dll");executeControl timeStep;writeControl timeStep;writeInterval 1;}\n'
(c/'system/functions').write_text(text,encoding='ascii')
e=dict(os.environ);e.update(json.loads(Path('tools/bluecfd-evaluation/isolated-environment.json').read_text()));e['OMP_NUM_THREADS']='1'
with (c/'postprocess-startup.log').open('x',encoding='utf-8') as log:
 r=subprocess.run([str(Path(e['FOAM_APPBIN'])/'foamPostProcess.exe'),'-case',str(c),'-solver','incompressibleFluid','-time','0.005'],env=e,stdout=log,stderr=subprocess.STDOUT,timeout=120)
assert r.returncode==0,(c/'postprocess-startup.log').read_text()[-2000:]
assert before=={n:sha(c/'0.005'/n) for n in names}
fields={}
for name in ['U','p','k','epsilon','nut']:
 p=c/'0.005'/name;data=p.read_text();m=re.search(r'internalField\s+nonuniform\s+List<(\w+)>\s+(\d+)\s*\(',data);assert m and int(m[2])==142480
 if m[1]=='vector':
  vals=[math.sqrt(math.fsum(float(x)**2 for x in a[1].split())) for a in itertools.islice(re.finditer(r'\(([^()]+)\)',data[m.end():]),142480)]
 else:vals=[float(x) for x in data[m.end():data.index(')',m.end())].split()]
 assert len(vals)==142480 and all(math.isfinite(v) for v in vals)
 if name in ['k','epsilon','nut']:assert min(vals)>=0
 fields[name]={'values':len(vals),'minimum':min(vals),'maximum':max(vals),'sha256':sha(p)}
log=(c/'foamRun.log').read_text();times=[Decimal(t) for t in re.findall(r'^Time = ([0-9.eE+-]+)s\s*$',log,re.M)]
assert times==[Decimal('.00025')*i for i in range(1,21)],times
flux={}
for name,target in policy['flow_m3_s'].items():
 files=list((c/'postProcessing'/('flux_'+name)).rglob('surfaceFieldValue.dat'));assert len(files)==1,(name,files)
 rows=[line.split() for line in files[0].read_text().splitlines() if line.strip() and not line.startswith('#')];assert len(rows)==1
 time_value,value=map(float,rows[0]);assert time_value==.005
 expected=-target if name=='inlet' else target
 assert math.isclose(value,expected,rel_tol=1e-12)
 flux[name]={'measured_outward_m3_s':value,'prescribed_outward_m3_s':expected,'relative_difference':(value-expected)/abs(expected)}
ypfiles=list((c/'postProcessing/wall_yPlus').rglob('yPlus.dat'));assert len(ypfiles)==1
yp=[a.split() for a in ypfiles[0].read_text().splitlines() if a.strip() and not a.startswith('#')];assert len(yp)==1 and yp[0][1]=='air_wall'
yplus=dict(zip(['minimum','maximum','average'],map(float,yp[0][2:])))
courants=[float(x) for x in re.findall(r'Courant Number mean: [^\s]+ max: ([^\s]+)',log)]
r={'scope':'Twenty physical-time startup steps only; no stationary statistics or design pressure','physical_times_exactly_match20prescribed_steps':True,'final_time_s':.005,'reference_residence_time_s':policy['nominal_residence_time_s'],'fraction_of_one_residence_time':.005/policy['nominal_residence_time_s'],'fields':fields,'native_postprocess_returncode':0,'all6primary_fields_unchanged_by_postprocess':True,'fluxes':flux,'net_outward_volume_flow_m3_s':math.fsum(v['measured_outward_m3_s'] for v in flux.values()),'native_yPlus_startup_only':yplus,'maximum_reported_Courant':max(courants) if courants else None,'old_SST_lowRe_yPlus_or_steady_window_reclassified':False,'near_wall_or_statistical_acceptance':False,'pressure_adopted':False,'design_accepted':False}
(c/'startup-field-and-flux-review.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in r.items() if k!='fields'}),flush=True)

from pathlib import Path
import re,math,json
case=Path(__file__).parent/'pitzDaily-prescribed-outlet-flow'
def body(p):return re.search(r'\n(\d+)\s*\n\(\s*\n(.*?)\n\)',p.read_text(),re.S)[2]
xyz=[tuple(map(float,a.split())) for a in re.findall(r'\(([^()]+)\)',body(case/'constant/polyMesh/points'))]
faces=[list(map(int,re.findall(r'\d+',a)))[1:] for a in body(case/'constant/polyMesh/faces').splitlines()]
b=(case/'constant/polyMesh/boundary').read_text();n,start=map(int,re.search(r'outlet\s*\{[^}]*nFaces\s+(\d+);\s*startFace\s+(\d+);',b).groups())
t=(case/'400/U').read_text();v=re.search(r'\boutlet\s*\{.*?value\s+nonuniform\s+List<vector>\s+\d+\s*\((.*?)\n\)',t,re.S)[1];vel=[tuple(map(float,a.split())) for a in re.findall(r'\(([^()]+)\)',v)];assert len(vel)==n
flux=[]
for face,v in zip(faces[start:start+n],vel):
 S=[0.,0.,0.];o=xyz[face[0]]
 for k in range(1,len(face)-1):
  a=[xyz[face[k]][j]-o[j] for j in range(3)];d=[xyz[face[k+1]][j]-o[j] for j in range(3)];c=[a[1]*d[2]-a[2]*d[1],a[2]*d[0]-a[0]*d[2],a[0]*d[1]-a[1]*d[0]];S=[x+y*.5 for x,y in zip(S,c)]
 flux.append(math.fsum(x*y for x,y in zip(S,v)))
rows={}
for name in ['inlet','outlet']:
 lines=(case/f'postProcessing/flux_{name}/289/surfaceFieldValue.dat').read_text().splitlines();rows[name]=[tuple(map(float,x.split())) for x in lines if x.strip() and not x.startswith('#') and float(x.split()[0])>=290];assert [int(x[0]) for x in rows[name]]==list(range(290,490))
q=.000254;err=max(abs(x[1]-q)/q for x in rows['outlet']);balance=max(abs(a[1]+b[1])/q for a,b in zip(rows['inlet'],rows['outlet']));native=math.fsum(flux)
assert err<1e-10 and balance<1e-10 and abs(native-q)/q<1e-10,(err,balance,native)
r={'scope':'Single-outlet prescribed-flow native verification; no physical or project pressure acceptance','backend':'OpenFOAM12 build12-8e8552546d20 serial blueCFD2024-1','boundary':'flowRateOutletVelocity volumetricFlowRate positive outward','target_m3_s':q,'pressure_boundaries':'zeroGradient all flow patches pRefCell0/pRefValue0','initial_native_convergence_iteration':289,'window':[290,489],'samples':200,'max_outlet_relative_error':err,'max_signed_flux_imbalance_relative':balance,'independent_saved_U_dot_Sf_m3_s':native,'independent_saved_field_time':400,'relative_algebra_check_target':1e-10,'multi_outlet_verified':False,'physical_validation':False,'project_pressure_accepted':False,'notes':['First controlDict observer ignored because system/functions exists; moved observer to system/functions, preserved failed observation log.','Continued same saved solution for200iterations with early residual stop removed only to collect flow window; no pressure stability claim.','Final489 fields not written at inherited100step cadence; independent field400 is inside observed window.']}
(case/'prescribed-flow-review.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))

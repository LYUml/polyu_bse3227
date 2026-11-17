from pathlib import Path
import runpy,re,math,json,itertools
from array import array
base=Path(__file__).parent;g=runpy.run_path(str(base/'verify_actual_pressure_observer.py'));case=g['case'];fields=g['fields'];patch=g['patch'];values=g['values'];owner=g['owner'];boundary=g['boundary']
name='outlet_1';b=patch(boundary,name);n=int(re.search(r'nFaces\s+(\d+);',b)[1]);start=int(re.search(r'startFace\s+(\d+);',b)[1]);u=values(patch(fields['U'],name),n,True);idx=max(range(n),key=lambda i:sum(x*x for x in u[i]));face_id=start+idx;cell=int(owner[face_id])
mesh=case/'constant/polyMesh'
def scalarbody(p):return re.search(r'\n\d+\s*\n\(\s*\n(.*?)\n\)',p.read_text(),re.S)[1]
xyz=[tuple(map(float,x.split())) for x in re.findall(r'\(([^()]+)\)',scalarbody(mesh/'points'))]
with (mesh/'faces').open() as f:
 for line in f:
  if line.strip().isdigit():break
 assert next(f).strip()=='('
 for i,line in enumerate(f):
  if i==face_id:face=list(map(int,re.findall(r'\d+',line)))[1:];break
S=[0.,0.,0.];o=xyz[face[0]]
for k in range(1,len(face)-1):
 a=[xyz[face[k]][j]-o[j] for j in range(3)];b=[xyz[face[k+1]][j]-o[j] for j in range(3)];cross=[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];S=[x+y*.5 for x,y in zip(S,cross)]
A=math.sqrt(sum(x*x for x in S));normal=[x/A for x in S];v=u[idx];vn=sum(x*y for x,y in zip(v,normal));vt=math.sqrt(max(0,sum(x*x for x in v)-vn*vn))
m=re.search(r'internalField\s+nonuniform\s+List<vector>\s+\d+\s*\(',fields['U']);matches=re.finditer(r'\(([^()]+)\)',fields['U'][m.end():]);internal=tuple(map(float,next(itertools.islice(matches,cell,cell+1))[1].split()))
nei=array('i',map(int,scalarbody(mesh/'neighbour').split()));faces_per_cell=sum(c==cell for c in owner)+sum(c==cell for c in nei)
sets={}
for p in (mesh/'sets').iterdir():
 if p.name in ['highAspectRatioCells','underdeterminedCells']:sets[p.name]=cell in set(map(int,scalarbody(p).split()))
r={'scope':'Saved unconverged11 spike localization only','patch':name,'patch_face_index':idx,'global_face_id':face_id,'owner_cell_id':cell,'face_area_m2':A,'vertex_average_m':[sum(xyz[i][j] for i in face)/len(face) for j in range(3)],'outward_normal':normal,'boundary_U_m_s':v,'boundary_normal_velocity_m_s':vn,'boundary_tangential_speed_m_s':vt,'owner_internal_U_m_s':internal,'owner_internal_speed_m_s':math.sqrt(sum(x*x for x in internal)),'owner_native_face_count':faces_per_cell,'owner_quality_set_membership':sets,'pressure_accepted':False}
(case/'velocity-spike-location.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))

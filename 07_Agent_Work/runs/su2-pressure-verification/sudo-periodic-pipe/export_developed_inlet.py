from pathlib import Path
import hashlib, io, json, math
import numpy as np
p=Path(__file__).parent
case=p/'nominal-cfl30-resumed'
assert 'Exit Success (SU2_CFD)' in (case/'developed.log').read_text(), 'Await normal solver terminal state'
raw=(case/'developed-restart.csv').read_bytes()
a=np.genfromtxt(io.BytesIO(raw),delimiter=',',names=True,deletechars='',autostrip=True)
h=np.genfromtxt(case/'developed-history.csv',delimiter=',',names=True,deletechars='',autostrip=True)
fields=('Pressure','Velocity_x','Velocity_y','Velocity_z','Turb_Kin_Energy','Omega')
assert len(a)==23484 and np.array_equal(a['PointID'],np.arange(len(a)))
assert all(np.isfinite(a[k]).all() for k in fields)
assert min(a['Turb_Kin_Energy'])>=0 and min(a['Omega'])>=0
assert all(h[k][-1]<=-10 for k in ('rms[P]','rms[U]','rms[V]','rms[W]','rms[k]','rms[w]'))
q=h['Avg_Massflow(inlet)'][-200:];target=.043736328010294444
assert len(q)==200 and np.all(np.diff(h['Inner_Iter'][-200:])==1)
assert max(abs(q/target-1))<=.001 and np.ptp(q)/np.mean(q)<.0001
mapping=json.loads((p/'developed-inlet-node-map.json').read_text())
original=p.parent/'sudo-upstream-baseline/sudo_coarse.su2'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(original.read_bytes())==mapping['original_mesh_sha256']
assert sha((p/'mesh.su2').read_bytes())==mapping['periodic_mesh_sha256']
mesh_lines=(p/'mesh.su2').read_text().splitlines()
mi=next(i for i,line in enumerate(mesh_lines) if line.strip().startswith('NPOIN='))
assert int(mesh_lines[mi].split('=')[1])==len(a)
for line in mesh_lines[mi+1:mi+1+len(a)]:
 parts=line.split();point_id=int(parts[3])
 assert math.dist(list(map(float,parts[:3])),[float(a[k][point_id]) for k in ('x','y','z')])<1e-12

groups={}
for i in range(len(a)): groups.setdefault((round(float(a['x'][i]),12),round(float(a['y'][i]),12)),[]).append(i)
assert len(groups)==618 and set(map(len,groups.values()))=={38}
spreads={k:max(float(np.ptp(a[k][v])) for v in groups.values()) for k in fields[1:]}
assert max(spreads[k] for k in fields[1:4])<1e-6 and spreads['Turb_Kin_Energy']<1e-6 and spreads['Omega']<.001
rows=[];vel={};original_vel={}
for node in mapping['nodes']:
 i=node['periodic_mesh_point_id'];old=node['source_mesh_point_id'];xyz=node['coordinate_m']
 assert math.dist(xyz,[float(a[k][i]) for k in ('x','y','z')])<1e-12
 v=np.array([a[k][i] for k in fields[1:4]]);speed=float(np.linalg.norm(v));normal=v/speed if speed else np.array([0.,0.,1.]);values=[*xyz,300.,speed,*normal,float(a['Turb_Kin_Energy'][i]),float(a['Omega'][i])]
 row=' '.join(format(x,'.17e') for x in values);parsed=list(map(float,row.split()));vel[old]=np.array(parsed[5:8])*parsed[4];original_vel[old]=v
 assert np.max(np.abs(vel[old]-v))<1e-12
 rows.append(row)
lines=original.read_text().splitlines();start=next(i for i,s in enumerate(lines) if s.strip().startswith('NPOIN='));n=int(lines[start].split('=')[1]);xyz={int((x:=s.split())[3]):np.array(list(map(float,x[:3]))) for s in lines[start+1:start+1+n]}
i=next(i for i,s in enumerate(lines) if s.strip()=='MARKER_TAG= inlet');count=int(lines[i+1].split('=')[1]);faces=[list(map(int,s.split())) for s in lines[i+2:i+2+count]]
flux=[0.,0.]
for face in faces:
 ids=face[1:];assert face[0]==9 and len(ids)==4
 center=sum((xyz[j] for j in ids))/4
 for k,j in enumerate(ids):
  v=xyz[j];before=(v+xyz[ids[(k-1)%4]])/2;after=(v+xyz[ids[(k+1)%4]])/2
  area=(np.linalg.norm(np.cross(after-v,center-v))+np.linalg.norm(np.cross(center-v,before-v)))/2
  flux[0]+=1.185*area*original_vel[j][2];flux[1]+=1.185*area*vel[j][2]
assert abs(flux[1]-flux[0])<1e-12 and abs(flux[1]/q[-1]-1)<1e-6
profile=('NMARK=1\nMARKER_TAG=inlet\nNROW=618\nNCOL=10\n# X Y Z TEMPERATURE VELOCITY NORMAL-X NORMAL-Y NORMAL-Z TKE DISSIPATION\n'+'\n'.join(rows)+'\n').encode()
report=dict(source_field_sha256=sha(raw),source_history_sha256=sha((case/'developed-history.csv').read_bytes()),native_node_mapping_sha256=sha((p/'developed-inlet-node-map.json').read_bytes()),profile_sha256=sha(profile),mass_flow_before_after_kg_s=flux,final_reported_mass_flow_kg_s=float(q[-1]),maximum_relative_nominal_flow_error=float(max(abs(q/target-1))),last200_relative_flow_range=float(np.ptp(q)/np.mean(q)),maximum_axial_spreads=spreads,all_six_residual_targets_pass=True,velocity_or_turbulence_rescaled=False,interpolation=False,engineering_accepted=False,scope='Numerically verified developed reference inlet only. Original experimental normalization, wall model and grid independence remain unaccepted. Temperature300K retained from official inlet; energy inactive.')
assert not (case/'developed-inlet.dat').exists() and not (case/'developed-inlet-review.json').exists()
with (case/'developed-inlet.dat').open('xb') as f:f.write(profile)
with (case/'developed-inlet-review.json').open('x') as f:json.dump(report,f,indent=2,allow_nan=False)
print(json.dumps(report))

from pathlib import Path
import re,json,gmsh,math
c=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/openfoam-pressure-verification/plenum-family-1-balanced-core-optimized');m=c/'constant/polyMesh'
gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.open(str(c/'air-exterior-gmsh22.msh'));tags,flat,_=gmsh.model.mesh.getNodes();source=[tuple(float(x) for x in flat[i:i+3]) for i in range(0,len(flat),3)];gmsh.finalize()
t=(m/'points').read_text();start=re.search(r'\n(\d+)\s*\n\(',t);assert start;points=[tuple(map(float,x.split())) for x in re.findall(r'\(([^()]+)\)',t[start.end():])];assert len(points)==int(start[1])==len(source);assert len(set(points))==len(points);index={tuple(round(x,12) for x in q):q for q in source};assert len(index)==len(source);assert len({tuple(round(x,12) for x in q) for q in points})==len(points);coordinate_error=max(abs(q[j]-index[tuple(round(x,12) for x in q)][j]) for q in points for j in range(3));assert coordinate_error<=1e-12
f=(m/'faces').read_text();start=re.search(r'\n(\d+)\s*\n\(',f);faces=[tuple(map(int,x.split())) for _,x in re.findall(r'(\d+)\(([^()]*)\)',f[start.end():])];assert len(faces)==int(start[1]);areas={}
for name in ['inlet','outlet_0','outlet_1','outlet_2','outlet_3']:
 block=re.search(r'\b'+name+r'\s*\{([^}]+)\}',(m/'boundary').read_text())[1];n=int(re.search(r'nFaces\s+(\d+)',block)[1]);s=int(re.search(r'startFace\s+(\d+)',block)[1]);a=[]
 for face in faces[s:s+n]:
  v=[0.,0.,0.]
  for i in range(len(face)):
   x=points[face[i]];y=points[face[(i+1)%len(face)]];v[0]+=x[1]*y[2]-x[2]*y[1];v[1]+=x[2]*y[0]-x[0]*y[2];v[2]+=x[0]*y[1]-x[1]*y[0]
  a.append(math.sqrt(sum(x*x for x in v))/2)
 areas[name]=math.fsum(a)
old=json.loads((c.parent/'plenum-family-1-resolution-core-optimized/port-area-comparison.json').read_text())['areas_m2']['plenum-family-1-resolution-core-optimized'];err=max(abs(areas[k]-old[k]) for k in areas);assert err<1e-11
r={'scope':'Native 17-digit import coordinate and five port-area correspondence only','native_points':len(points),'all_source_coordinates_exact':coordinate_error==0,'maximum_coordinate_difference_m':coordinate_error,'coordinate_correspondence_unique':True,'coordinate_tolerance_m':1e-12,'initial_exact_equality_check_failed':True,'areas_m2':areas,'maximum_absolute_area_difference_m2':err,'engineering_accepted':False};(c/'native-coordinate-port-review.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))

import gmsh,json,math
from pathlib import Path
p=Path(__file__).parent
b=json.loads((p/'boundary-source.json').read_text());gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.model.add('bounded-air');v=gmsh.model.occ.importShapes(str(p/'actual-air.brep'));gmsh.model.occ.synchronize()
surfaces=gmsh.model.getBoundary(v,combined=True,oriented=False);used=set();reviews=[]
for i,x in enumerate(b):
 matches=[t for _,t in surfaces if math.dist(gmsh.model.occ.getCenterOfMass(2,t),x['origin_m'])<1e-7 and abs(gmsh.model.occ.getMass(2,t)-x['clear_area_m2'])<1e-8]
 if len(matches)!=1:raise ValueError((x['guid'],matches))
 tag=matches[0]
 if gmsh.model.getType(2,tag)!='Plane':raise ValueError('not planar')
 points=gmsh.model.getBoundary([(2,tag)],combined=True,oriented=False,recursive=True)
 errors=[abs(sum((float(a)-o)*n for a,o,n in zip(gmsh.model.getValue(0,t,[]),x['origin_m'],x['outward_normal']))) for _,t in points]
 if len(points)!=4 or max(errors)>1e-8:raise ValueError('cap vertex planes differ')
 normal=gmsh.model.getNormal(tag,[0.,0.]);dot=sum(float(a)*n for a,n in zip(normal,x['outward_normal']))
 # CAD parametrization normal can be reversed; require parallelism here.
 if abs(abs(dot)-1)>1e-8 or tag in used:raise ValueError('cap normal/identity differs')
 used.add(tag);name='inlet' if x['direction']=='SINK' else 'outlet_'+str(i);gmsh.model.addPhysicalGroup(2,[tag],name=name)
 reviews.append(dict(x,surface_tag=tag,marker=name,area_m2=gmsh.model.occ.getMass(2,tag),max_vertex_plane_error_m=max(errors),parametric_normal_dot_source=dot))
wall=[tag for _,tag in surfaces if tag not in used];gmsh.model.addPhysicalGroup(2,wall,name='wall');gmsh.model.addPhysicalGroup(3,[t for _,t in v],name='fluid')
gmsh.option.setNumber('General.NumThreads',4);gmsh.option.setNumber('Mesh.MeshSizeMin',.035);gmsh.option.setNumber('Mesh.MeshSizeMax',.15);gmsh.option.setNumber('Mesh.MeshSizeFromCurvature',12)
gmsh.model.mesh.generate(3);gmsh.model.mesh.optimize('Netgen');gmsh.write(str(p/'bounded-initial-air.su2'))
r={'caps':reviews,'wall_surfaces':len(wall),'all_exterior_surfaces':len(surfaces),'pressure_accepted':False,'near_wall_mesh_accepted':False,'normal_scope':'CAD parallelism only; exported mesh outward orientation still needs verification'}
(p/'boundary-review.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2));gmsh.finalize()

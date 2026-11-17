import argparse,json,os,hashlib
from pathlib import Path
import gmsh
p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--nx',type=int,default=49);p.add_argument('--ny',type=int,default=33);a=p.parse_args();O=Path(a.output).resolve();root=Path(os.environ['BSA_PROJECT_ROOT']).resolve();assert O.is_relative_to(root) and not O.exists() and a.nx>2 and a.ny>2;O.mkdir(parents=True);assert gmsh.__version__=='4.15.2';gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.model.add('periodic-channel-analytic-benchmark');g=gmsh.model.geo;pts=[g.addPoint(x,y,0) for x,y in [(0,0),(1,0),(1,.1),(0,.1)]];lines=[g.addLine(pts[i],pts[(i+1)%4]) for i in range(4)];surf=g.addPlaneSurface([g.addCurveLoop(lines)]);g.synchronize()
for line,n in zip(lines,[a.nx,a.ny,a.nx,a.ny]):gmsh.model.mesh.setTransfiniteCurve(line,n)
gmsh.model.mesh.setTransfiniteSurface(surf);gmsh.model.mesh.setRecombine(2,surf)
for name,tags in [('inlet',[lines[3]]),('outlet',[lines[1]]),('wall',[lines[0],lines[2]])]:
 tag=gmsh.model.addPhysicalGroup(1,tags);gmsh.model.setPhysicalName(1,tag,name)
tag=gmsh.model.addPhysicalGroup(2,[surf]);gmsh.model.setPhysicalName(2,tag,'fluid');gmsh.model.mesh.generate(2);gmsh.write(str(O/'mesh.su2'));nodes,coords,_=gmsh.model.mesh.getNodes();types,tags,ns=gmsh.model.mesh.getElements(2);report=dict(gmsh_version=gmsh.__version__,nodes=len(nodes),elements=sum(len(t) for t in tags),element_types=list(map(int,types)),length_m=1.,height_m=.1,nx=a.nx,ny=a.ny,source='Analyticalbenchmark geometry,notcourseworkdesign',mesh_sha256=hashlib.sha256((O/'mesh.su2').read_bytes()).hexdigest());gmsh.finalize();(O/'mesh-review.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))

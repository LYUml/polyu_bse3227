import gmsh,json
from pathlib import Path
p=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/su2-pressure-verification/actual-native-air-domain');gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.option.setNumber('General.NumThreads',4);gmsh.model.add('layer-prototype');v=gmsh.model.occ.importShapes(str(p/'actual-air.brep'));gmsh.model.occ.synchronize();surfs=gmsh.model.getBoundary(v,oriented=False);gmsh.model.occ.remove(v,recursive=False);gmsh.model.occ.synchronize();gmsh.option.setNumber('Mesh.MeshSizeMax',.15);gmsh.option.setNumber('Mesh.MeshSizeMin',.035)
heights=[];h=0
for i in range(22):h+=0.00001*1.3**i;heights.append(-h)
try:
 ex=gmsh.model.geo.extrudeBoundaryLayer(surfs,[1]*22,heights,True);gmsh.model.geo.synchronize();tops=[ex[i-1][1] for i in range(1,len(ex)) if ex[i][0]==3];loop=gmsh.model.geo.addSurfaceLoop(tops);core=gmsh.model.geo.addVolume([loop]);gmsh.model.geo.synchronize();gmsh.model.mesh.generate(3);gmsh.write(str(p/'wall-refined-prototype.msh'));print('mesh success',len(gmsh.model.mesh.getNodes()[0]))
except Exception as e:
 (p/'wall-refined-error.txt').write_text(str(e));print(type(e).__name__,str(e))
finally:gmsh.finalize()

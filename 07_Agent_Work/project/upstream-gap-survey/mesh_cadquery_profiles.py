"""Exact upstream CAD shapes to compact shared mesh profiles, fixed SI accuracy."""
import hashlib,json
from pathlib import Path
import cadquery as cq
import numpy as np
from OCP.BRepTools import BRepTools
from OCP.BRepMesh import BRepMesh_IncrementalMesh

RUN=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/rect-round-cadquery')
OUT=RUN/'compact-meshes';OUT.mkdir(exist_ok=False)
cases=json.loads((RUN/'input.json').read_text())['cases'];groups={};records=[]
for row in cases:
    key=tuple(row[k] for k in ['width_m','height_m','diameter_m','section_offset_m','taper_length_m','start_length_m','end_length_m'])
    if key not in groups:
        name='PROFILE-'+str(len(groups)+1);groups[key]=name
        source=RUN/'kernel'/(row['id']+'.brep')
        # OCCT modelling in mm improves numerical scaling; all outputs convert
        # back to m. Absolute deflection.01mm = existing10micrometre policy.
        shape=cq.Shape.importBrep(str(source)).scale(1000)
        BRepTools.Clean_s(shape.wrapped)
        mesher=BRepMesh_IncrementalMesh(shape.wrapped,.01,False,.02)
        assert mesher.IsDone()
        vertices,faces=shape.tessellate(.01,.02)
        target=OUT/(name+'.npz')
        np.savez_compressed(target,vertices=np.array([v.toTuple() for v in vertices])/1000,faces=np.array(faces))
        records.append(dict(profile=name,source_case=row['id'],brep_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            mesh_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),vertices=len(vertices),faces=len(faces),
            absolute_deflection_m=.00001,angular_deflection=.02,coordinates_unit='m'))
        print(name,len(vertices),len(faces),flush=True)
    row['profile']=groups[key]
(OUT/'mesh-review.json').write_text(json.dumps(dict(profiles=records,cases=cases,
    geometry_source='Exact CadQuery2.6.1/OCP7.8.1.1.post1 BRep; OCCT absolute meshing in mm with unchanged10micrometre/.02rad targets',
    worker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2))

"""Reopen actual CadQuery BReps as analytic IFC and independently audit caps."""
import hashlib,json,math
from pathlib import Path
import numpy as np
import ifcopenshell
import ifcopenshell.api as api
import ifcopenshell.geom as geom
import ifcopenshell.validate
from ifcopenshell.util.element import replace_attribute
from bsa.circular_geometry import configure
from bsa.solid_clash import from_mesh

RUN=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/rect-round-cadquery')
spec=json.loads((RUN/'input.json').read_text());kernel=json.loads((RUN/'kernel/kernel-review.json').read_text())
OUT=RUN/'native-final';OUT.mkdir(exist_ok=False)
reviews=[]
for row,proof in zip(spec['cases'],kernel['results']):
    assert row['id']==proof['id']
    source=RUN/'kernel'/(row['id']+'.brep')
    assert hashlib.sha256(source.read_bytes()).hexdigest()==proof['brep_sha256']
    model=api.run('project.create_file',version='IFC4');api.run('root.create_entity',model,ifc_class='IfcProject',name='Source-bound round inlet transition candidate')
    api.run('unit.assign_unit',model,units=[api.run('unit.add_si_unit',model,unit_type='LENGTHUNIT')])
    context=api.run('context.add_context',model,context_type='Model')
    body=api.run('context.add_context',model,context_type='Model',context_identifier='Body',target_view='MODEL_VIEW',parent=context)
    obj=api.run('root.create_entity',model,ifc_class='IfcDuctFitting',predefined_type='TRANSITION',name=row['id']+'-RECT-ROUND')
    shape=model.add(geom.serialise('IFC4',source.read_text(),True))
    assert shape.is_a('IfcProductDefinitionShape')
    for rep in shape.Representations:rep.ContextOfItems=body
    obj.Representation=shape
    api.run('geometry.edit_object_placement',model,product=obj,matrix=np.eye(4),is_si=True)
    # Native serialiser emits distinct vertices at mathematically identical
    # coordinates. IFC edge loops require shared entity identity, not merely
    # coincident coordinates. Unify exact coordinate tuples only, with no
    # tolerance snapping, and keep the rejected original native trial.
    canonical={};duplicates=0
    for vertex in list(model.by_type('IfcVertexPoint')):
        key=tuple(vertex.VertexGeometry.Coordinates)
        if key not in canonical:canonical[key]=vertex;continue
        for inverse in list(model.get_inverse(vertex)):replace_attribute(inverse,vertex,canonical[key])
        model.remove(vertex);duplicates+=1
    target=OUT/(row['id']+'.ifc');model.write(str(target))
    saved=ifcopenshell.open(str(target));logger=ifcopenshell.validate.json_logger()
    ifcopenshell.validate.validate(saved,logger,express_rules=True)
    assert not logger.statements,logger.statements[:2]
    settings=geom.settings();configure(settings)
    mesh=geom.create_shape(settings,saved.by_guid(obj.GlobalId))
    vertices=np.array(mesh.geometry.verts).reshape(-1,3);faces=np.array(mesh.geometry.faces).reshape(-1,3)
    solid=from_mesh((vertices,faces));volume=solid.volume()
    assert math.isclose(volume,proof['volume_m3'],rel_tol=.002,abs_tol=1e-9)
    a=row['start_length_m'];end=row['taper_length_m']+row['end_length_m'];t=row['section_offset_m']
    rect=vertices[np.abs(vertices[:,2]+a)<1e-8];circle=vertices[np.abs(vertices[:,2]-end)<1e-8]
    assert len(rect)>=8 and len(circle)>32
    expected_bounds=np.array([-row['width_m']/2-t,-row['height_m']/2-t,row['width_m']/2+t,row['height_m']/2+t])
    assert np.allclose(np.r_[rect[:,:2].min(axis=0),rect[:,:2].max(axis=0)],expected_bounds,atol=1e-8,rtol=0)
    radius=np.linalg.norm(circle[:,:2],axis=1);inner=row['diameter_m']/2
    assert np.all(np.minimum(abs(radius-inner),abs(radius-inner-t))<1e-8)
    assert np.any(abs(radius-inner)<1e-8) and np.any(abs(radius-inner-t)<1e-8)
    ring=circle[abs(radius-inner)<1e-8]
    angles=np.sort(np.unique(np.arctan2(ring[:,1],ring[:,0])));gaps=np.diff(np.r_[angles,angles[0]+2*math.pi])
    sag=inner*(1-math.cos(max(gaps)/2));assert sag<=.00002
    reviews.append(dict(id=row['id'],ifc_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        exact_duplicate_vertex_entities_shared=duplicates,
        schema_express_pass=True,native_closed_positive_wall=True,mesh_volume_m3=volume,
        kernel_volume_m3=proof['volume_m3'],rectangle_outer_cap_bounds_match=True,
        circle_inner_outer_radii_match=True,circle_mesh_chord_error_m=sag,
        native_representation_types=[r.RepresentationType for r in obj.Representation.Representations],
        analytic_curve_types=sorted({e.is_a() for e in saved.by_type('IfcCurve')}),design_accepted=False))
result=dict(cases=reviews,source_sha256=kernel['source_sha256'],
    total_pressure_loss_verified=False,assembly_connections_verified=False,
    scope='Actual analytic IFC advanced BRep round/rectangle transition candidates; walls section-offset, not sheet-normal constant thickness')
(RUN/'native-review.json').write_text(json.dumps(result,indent=2))
print(json.dumps(dict(cases=len(reviews),schema_and_native_caps_pass=True,max_chord_error_m=max(r['circle_mesh_chord_error_m'] for r in reviews))))

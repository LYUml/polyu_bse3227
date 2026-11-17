"""Try the verified hollow-wall CSG composition on exact upstream loft solids."""
from pathlib import Path
import numpy as np
import ifcopenshell
import ifcopenshell.api as api
import ifcopenshell.geom as geom
import ifcopenshell.validate
from ifcopenshell.util.element import replace_attribute
from bsa.circular_geometry import configure
from bsa.solid_clash import from_mesh

OUT=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/rect-round-cadquery/csg-probe')
model=api.run('project.create_file',version='IFC4');api.run('root.create_entity',model,ifc_class='IfcProject',name='CadQuery CSG source probe')
api.run('unit.assign_unit',model,units=[api.run('unit.add_si_unit',model,unit_type='LENGTHUNIT')])
context=api.run('context.add_context',model,context_type='Model')
body=api.run('context.add_context',model,context_type='Model',context_identifier='Body',target_view='MODEL_VIEW',parent=context)
operands=[]
for name in ['outer','inner']:
    representation=geom.serialise('IFC4',(OUT/(name+'.brep')).read_text(),True)
    assert len(representation.Representations[0].Items)==1
    operands.append(model.add(representation.Representations[0].Items[0]))
canonical={}
for vertex in list(model.by_type('IfcVertexPoint')):
    key=tuple(vertex.VertexGeometry.Coordinates)
    if key not in canonical:canonical[key]=vertex;continue
    for inverse in list(model.get_inverse(vertex)):replace_attribute(inverse,vertex,canonical[key])
    model.remove(vertex)
wall=model.create_entity('IfcBooleanResult',Operator='DIFFERENCE',FirstOperand=operands[0],SecondOperand=operands[1])
rep=model.create_entity('IfcShapeRepresentation',ContextOfItems=body,RepresentationIdentifier='Body',RepresentationType='CSG',Items=[wall])
obj=api.run('root.create_entity',model,ifc_class='IfcDuctFitting',predefined_type='TRANSITION',name='CadQuery positive loft CSG')
api.run('geometry.assign_representation',model,product=obj,representation=rep)
api.run('geometry.edit_object_placement',model,product=obj,matrix=np.eye(4),is_si=True)
target=OUT/'candidate-reviewed.ifc';assert not target.exists();model.write(str(target))
saved=ifcopenshell.open(str(target));logger=ifcopenshell.validate.json_logger()
ifcopenshell.validate.validate(saved,logger,express_rules=True);assert not logger.statements,logger.statements[:1]
settings=geom.settings();configure(settings)
shape=geom.create_shape(settings,saved.by_guid(obj.GlobalId))
v=np.array(shape.geometry.verts).reshape(-1,3);f=np.array(shape.geometry.faces).reshape(-1,3)
solid=from_mesh((v,f))
print('CSG native volume',solid.volume(),'IFCbytes',target.stat().st_size,'vertices',len(v))

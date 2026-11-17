"""Execute existing pinned IFC upstream on actual source profile combinations."""
import hashlib,json,math
from pathlib import Path
import ifcopenshell
import ifcopenshell.api as api
import ifcopenshell.geom
import ifcopenshell.util.shape_builder as upstream
import numpy as np

BASE=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs')
OUT=BASE/'rect-round-upstream-probe';OUT.mkdir(exist_ok=False)
revision=json.loads((BASE/'vav-manufacturer-capacity/inlet-revision.json').read_text())
nodes={n['node']:n for n in json.loads((BASE/'recentered-vav-connection-schedule/revised-junction.json').read_text())['nodes']}
results=[]
for row in revision['rows']:
    inc=nodes[row['id']]['incidents'][0];w,h=inc['width_m'],inc['height_m'];diameter=row['revised_candidate_size_in']*.0254
    model=api.run('project.create_file',version='IFC4');api.run('root.create_entity',model,ifc_class='IfcProject')
    api.run('unit.assign_unit',model,units=[api.run('unit.add_si_unit',model,unit_type='LENGTHUNIT')])
    context=api.run('context.add_context',model,context_type='Model')
    api.run('context.add_context',model,context_type='Model',context_identifier='Body',target_view='MODEL_VIEW',parent=context)
    segments=[]
    for profile in [model.create_entity('IfcRectangleProfileDef',ProfileType='AREA',XDim=w,YDim=h),model.create_entity('IfcCircleProfileDef',ProfileType='AREA',Radius=diameter/2)]:
        element=api.run('root.create_entity',model,ifc_class='IfcDuctSegment')
        material=model.create_entity('IfcMaterialProfileSet',MaterialProfiles=[model.create_entity('IfcMaterialProfile',Profile=profile)])
        model.create_entity('IfcRelAssociatesMaterial',GlobalId=ifcopenshell.guid.new(),RelatedObjects=[element],RelatingMaterial=material)
        segments.append(element)
    representation,parameters=upstream.ShapeBuilder(model).mep_transition_shape(*segments,.05,.05,angle=30.)
    if representation is None:
        results.append(dict(id=row['id'],status='upstream_length_or_shape_rejected'));continue
    circle_item=representation.Items[1]
    points=np.asarray(circle_item.Coordinates.CoordList)
    ring=np.unique(points[:,:2],axis=0)
    angles=np.sort(np.arctan2(ring[:,1],ring[:,0]));gaps=np.diff(np.r_[angles,angles[0]+2*math.pi])
    error=diameter/2*(1-math.cos(max(gaps)/2))
    results.append(dict(id=row['id'],rectangle_m=[w,h],diameter_m=diameter,upstream_parameters={k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in parameters.items()},
        circle_vertices=len(ring),maximum_chord_error_m=error,within_existing20micrometre_cap_budget=error<=.00002,
        status='faceted_circle_mismatch' if error>.00002 else 'profile_candidate'))
    if row['id']=='VAV-01':model.write(str(OUT/'upstream-profile-probe.ifc'))
result=dict(upstream_version=ifcopenshell.version,upstream_sha256=hashlib.sha256(Path(upstream.__file__).read_bytes()).hexdigest(),
    profiles=results,adopted=False,reason='Unmodified upstream uses16circle vertices; no tolerance relaxation or package patch applied')
(OUT/'probe.json').write_text(json.dumps(result,indent=2))
print(json.dumps(dict(cases=len(results),mismatches=sum(r['status']=='faceted_circle_mismatch' for r in results),length_rejections=sum(r['status']=='upstream_length_or_shape_rejected' for r in results))))

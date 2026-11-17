"""Actual material cap audit on the complete mixed-profile inlet network."""
import hashlib,json,math
from pathlib import Path
import numpy as np
import ifcopenshell,ifcopenshell.geom as geom
from ifcopenshell.util import placement,system
from bsa.interface_contacts import cap,matching
from bsa.circular_geometry import configure

RUN=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/recentered-constant-height-network')
record=json.loads((RUN/'integration.json').read_text());IFC=RUN/'Supply Network.ifc'
record['ifc_sha256']=hashlib.sha256(IFC.read_bytes()).hexdigest()
model=ifcopenshell.open(str(IFC));settings=geom.settings();settings.set(settings.USE_WORLD_COORDS,True);configure(settings)
meshes={};records=[]
def mesh(obj):
    if obj.GlobalId not in meshes:
        shape=geom.create_shape(settings,obj)
        meshes[obj.GlobalId]=(np.asarray(shape.geometry.verts).reshape(-1,3),np.asarray(shape.geometry.faces).reshape(-1,3))
    return meshes[obj.GlobalId]
def circular(v,f,frame):
    local=(v-frame[:3,3])@frame[:3,:3]
    selected=f[np.max(abs(local[f,2]),axis=1)<1e-8]
    assert len(selected)>0
    points=local[np.unique(selected),:2];radius=np.linalg.norm(points,axis=1)
    inner,outer=float(radius.min()),float(radius.max());assert 0<inner<outer
    assert np.max(np.minimum(abs(radius-inner),abs(radius-outer)))<1e-8
    sag=[]
    for r in [inner,outer]:
        ring=points[abs(radius-r)<1e-8];angles=np.sort(np.unique(np.arctan2(ring[:,1],ring[:,0])))
        gaps=np.diff(np.r_[angles,angles[0]+2*math.pi]);sag.append(r*(1-math.cos(max(gaps)/2)))
    assert max(sag)<.00002
    triangles=local[selected]
    area=float(np.linalg.norm(np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]),axis=1).sum()/2)
    assert math.isclose(area,math.pi*(outer**2-inner**2),rel_tol=.002)
    return dict(inner_radius_m=inner,outer_radius_m=outer,area_m2=area,max_chord_error_m=max(sag))
for link in model.by_type('IfcRelConnectsPorts'):
    ports=[link.RelatingPort,link.RelatedPort];objects=[system.get_port_element(p) for p in ports]
    frames=[placement.get_local_placement(p.ObjectPlacement) for p in ports]
    assert ports[0].FlowDirection=='SOURCE' and ports[1].FlowDirection=='SINK'
    assert np.allclose(frames[0][:3,3],frames[1][:3,3],atol=1e-8,rtol=0)
    assert np.allclose(frames[0][:3,2],-frames[1][:3,2],atol=1e-8,rtol=0)
    is_circle=any(o.is_a('IfcDuctSegment') and o.Representation.Representations[0].Items[0].SweptArea.is_a('IfcCircleHollowProfileDef') for o in objects)
    if is_circle:
        data=[circular(*mesh(o),frame) for o,frame in zip(objects,frames)]
        for key in ['inner_radius_m','outer_radius_m']:assert abs(data[0][key]-data[1][key])<1e-8
        detail=dict(kind='circular',native_annulus_radii_match=True,maximum_pair_chord_error_m=max(d['max_chord_error_m'] for d in data))
    else:
        data=[]
        for obj,frame in zip(objects,frames):
            v,f=mesh(obj);local=(v-frame[:3,3])@frame[:3,:3]
            selected=f[np.max(abs(local[f,2]),axis=1)<1e-8]
            data.append(cap(v,selected,frame))
        matching(*data);detail=dict(kind='rectangular',native_material_corner_and_area_match=True)
    records.append(dict(port_guids=[p.GlobalId for p in ports],body_guids=[o.GlobalId for o in objects],**detail))
assert len(records)==109 and sum(r['kind']=='circular' for r in records)==0
result=dict(ifc_sha256=record['ifc_sha256'],interfaces=records,rectangular_caps_match=109,circular_caps_match=0,
    port_frames_match=True,native_material_caps_match=True,product_joints_verified=False,
    complete_pressure_verified=False,design_accepted=False)
out=RUN/'native-cap-review.json';assert not out.exists();out.write_text(json.dumps(result,indent=2))
print(json.dumps(dict(rectangular_interfaces=109,circular_interfaces=0,all109actual_caps_match=True)))

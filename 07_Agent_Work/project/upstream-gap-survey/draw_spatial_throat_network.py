"""Native horizontal material section of the saved mixed-profile whole network."""
import hashlib,json
from pathlib import Path
import numpy as np
import ifcopenshell,ifcopenshell.geom as geom
from ifcopenshell.util import placement,system
import trimesh,ezdxf
from bsa.circular_geometry import configure
from bsa.ifc_native import run as native

RUN=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/tee-throat-spatial-network')
IFC=RUN/'Supply Network.ifc';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
caps=json.loads((RUN/'native-cap-review.json').read_text());assert caps['ifc_sha256']==sha(IFC)
raw=json.loads((RUN/'raw-clash/clash.json').read_text());assert raw['intersection_pair_count']==0
pressure=json.loads((RUN/'pressure-reviewed/review.json').read_text());assert pressure['ifc_sha256']==sha(IFC)
OUT=RUN/'drawing';OUT.mkdir(exist_ok=False)
model=ifcopenshell.open(str(IFC));settings=geom.settings();configure(settings);settings.set(settings.USE_WORLD_COORDS,True)
sections=[];bounds=[]
for obj in model.by_type('IfcDistributionElement'):
    shape=geom.create_shape(settings,obj);v=np.asarray(shape.geometry.verts).reshape(-1,3);f=np.asarray(shape.geometry.faces).reshape(-1,3)
    mesh=trimesh.Trimesh(vertices=v,faces=f,process=False)
    segments=trimesh.intersections.mesh_plane(mesh,[0,0,1],[0,0,0])
    assert len(segments)>0
    sections.append((obj.GlobalId,segments));bounds.append(v)
allv=np.vstack(bounds);lo=allv.min(axis=0);hi=allv.max(axis=0);span=hi-lo
scale=next(s for s in [200,250,300,400] if span[0]<.27*s and span[1]<.14*s)
offset=np.array([.01*scale,.03*scale])-lo[:2]
doc=ezdxf.new('R2018');doc.units=6;doc.appids.new('BSA_IFC');msp=doc.modelspace()
for layer in ['BSA_MATERIAL_SECTION','BSA_SECTION_REFERENCE','BSA_VAV_LABEL']:doc.layers.new(layer)
counts={}
for guid,segments in sections:
    counts[guid]=0
    for segment in segments:
        xy=segment[:,:2]+offset
        if np.linalg.norm(xy[1]-xy[0])<1e-10:continue
        e=msp.add_line(tuple(xy[0]),tuple(xy[1]),dxfattribs={'layer':'BSA_MATERIAL_SECTION'})
        e.set_xdata('BSA_IFC',[(1000,guid)]);counts[guid]+=1
assert len(counts)==132 and all(counts.values())
local=json.loads((RUN.parent/'rect-round-sourced-design/analytic-inlet-assemblies/author-review.json').read_text())
for row in local['cases']:
    p=model.by_guid(row['round_ports']['outlet']['guid']);point=placement.get_local_placement(p.ObjectPlacement)[:2,3]+offset
    e=msp.add_text(row['id'],dxfattribs={'height':.0018*scale,'insert':tuple(point+[.15,-.45]),'layer':'BSA_VAV_LABEL'})
    e.set_xdata('BSA_IFC',[(1000,row['round_guid'])])
def text(value,y,size=.0024):msp.add_text(value,dxfattribs={'height':size*scale,'insert':(.01*scale,y*scale)})
text('SUPPLY NETWORK WITH VAV INLETS',.191,.004)
text('Actual saved horizontal material section at assumed z=0 | scale1:'+str(scale),.182)
text('132 bodies;20outlets;full pressure unresolved (29fitting paths)',.173)
text('Nominal profiles, gauge and equipment inlet positions remain study assumptions',.012,.002)
text('VAV internals, outlet plenums, flex, architecture and installed clearance remain unverified',.005,.0019)
ref=msp.add_line((.01*scale,.024*scale),(.01*scale+10,.024*scale),dxfattribs={'layer':'BSA_SECTION_REFERENCE'})
ref.set_xdata('BSA_IFC',[(1000,sections[0][0])])
msp.add_text('10m reference',dxfattribs={'height':.0024*scale,'insert':(.01*scale+10+.005*scale,.023*scale)})
dxf=OUT/'Supply Network with VAV Inlets.dxf';doc.saveas(dxf)
sheet=dict(source='Saved132body IFC actual horizontal material sections; inherited reference elevation is not installed height',
    window_drawing_units=[0,0,.29*scale,.20*scale],scale_denominator=scale,
    reference_ifc_guid=sections[0][0],reference_layer='BSA_SECTION_REFERENCE',drawing_name='section',pdf_tolerance_mm=.3)
(OUT/'sheet.json').write_text(json.dumps(sheet,indent=2))
result=native(dxf,OUT/'sheet.json',OUT/'native')
(OUT/'projection.json').write_text(json.dumps(dict(ifc_sha256=sha(IFC),native_product_section_counts=counts,
    represented_products=132,boundary_labels=20,scale=scale,native_reopen_pass=result['native_reopen_pass'],
    actual_PDF_visual_review='pending',design_accepted=False),indent=2))
print(json.dumps(dict(native_reopen_pass=result['native_reopen_pass'],products=132,labels=20)))

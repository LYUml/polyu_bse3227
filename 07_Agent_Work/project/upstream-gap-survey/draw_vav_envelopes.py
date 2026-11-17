"""Saved-native envelope projection through the existing AutoCAD adapter."""
import hashlib,json
from pathlib import Path
import numpy as np
import ifcopenshell,ifcopenshell.geom
import ezdxf
from bsa.source_network_drawing import project
from bsa.ifc_native import run

RUN=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/vav-finite-placement')
IFC=RUN/'model.ifc';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
review=json.loads((RUN/'native-review.json').read_text());assert sha(IFC)==review['ifc_sha256']
placement=json.loads((RUN/'placement.json').read_text())
kinds={r['guid']:('CASING' if r['id'].endswith('CASING') else 'INLET' if r['id'].endswith('INLET-RESERVATION') else 'ACCESS') for r in placement['obstacles']}
OUT=RUN/'drawing-final';OUT.mkdir(exist_ok=False)
model=ifcopenshell.open(str(IFC));settings=ifcopenshell.geom.settings();settings.set(settings.USE_WORLD_COORDS,True)
items=[];allverts=[]
for e in model.by_type('IfcElement'):
    if not e.Representation:continue
    shape=ifcopenshell.geom.create_shape(settings,e)
    vertices=np.asarray(shape.geometry.verts).reshape(-1,3);faces=np.asarray(shape.geometry.faces).reshape(-1,3)
    items.append((e.GlobalId,project(vertices,faces)));allverts.append(vertices)
assert len(items)==169
points=np.vstack(allverts);lo=points.min(axis=0);hi=points.max(axis=0);span=hi-lo
scale=next(s for s in (200,250,300,400) if span[0]<=.27*s and span[1]<=.14*s)
offset=np.array([.01*scale,.030*scale])-lo[:2]
doc=ezdxf.new('R2018');doc.units=6;doc.appids.new('BSA_IFC');msp=doc.modelspace()
for layer,color in [('NETWORK',8),('CASING',3),('INLET',1),('ACCESS',5),('SECTION_REFERENCE',7)]:doc.layers.new('BSA_'+layer,dxfattribs={'color':color})
doc.linetypes.new('BSA_RESERVATION',dxfattribs={'description':'Reserved space','pattern':[.20,.12,-.08]})
counts={}
for guid,polygons in items:
    counts[guid]=0
    for polygon in polygons:
        for ring in [polygon.exterior,*polygon.interiors]:
            entity=msp.add_lwpolyline((np.asarray(ring.coords)[:-1]+offset).tolist(),close=True,
                dxfattribs={'layer':'BSA_'+kinds.get(guid,'NETWORK'),'linetype':'BSA_RESERVATION' if kinds.get(guid) in ['INLET','ACCESS'] else 'Continuous','lineweight':35 if kinds.get(guid)=='CASING' else 9})
            entity.set_xdata('BSA_IFC',[(1000,guid)]);counts[guid]+=1
assert all(counts.values())
def text(value,y,height=.0022):msp.add_text(value,dxfattribs={'height':height*scale,'insert':(.01*scale,y*scale)})
text('VAV EQUIPMENT SPACE STUDY',.191,.004)
text('Solid: network and casing | Dashed: inlet and both-side access reservation',.182)
text('20 candidate units | nominal inlet12/14in | scale1:'+str(scale),.173)
text('Inlet datum and z=0 are study assumptions; no connected equipment or installation acceptance',.012,.0019)
text('20 upstream duct replacements required; architecture, plenums, flex and full pressure unresolved',.005,.0019)
ref=msp.add_line((.01*scale,.024*scale),(.01*scale+10,.024*scale),dxfattribs={'layer':'BSA_SECTION_REFERENCE'})
ref.set_xdata('BSA_IFC',[(1000,items[0][0])])
msp.add_text('10m',dxfattribs={'height':.0025*scale,'insert':(.01*scale+10+.005*scale,.023*scale)})
dxf=OUT/'VAV Equipment Space.dxf';doc.saveas(dxf)
sheet=dict(source='Actual saved candidate IFC mesh projection; source-coordinate translation only; no equipment connectivity accepted',
    window_drawing_units=[0,0,.29*scale,.20*scale],scale_denominator=scale,
    reference_ifc_guid=items[0][0],reference_layer='BSA_SECTION_REFERENCE',drawing_name='section',pdf_tolerance_mm=.3)
(OUT/'sheet.json').write_text(json.dumps(sheet,indent=2))
native=run(dxf,OUT/'sheet.json',OUT/'native')
(OUT/'projection.json').write_text(json.dumps(dict(ifc_sha256=sha(IFC),dxf_sha256=sha(dxf),
    contours_per_guid=counts,component_count=169,native_reopen_pass=native['native_reopen_pass'],
    scale=scale,actual_plot_visually_reviewed=False,design_accepted=False),indent=2))
print(json.dumps(dict(components=169,native_reopen_pass=native['native_reopen_pass'],scale=scale)))

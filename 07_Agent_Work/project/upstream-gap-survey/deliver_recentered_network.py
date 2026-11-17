"""Native coordination drawing of the actual rebased saved network."""
import hashlib,json
from pathlib import Path
import numpy as np
import ifcopenshell,ifcopenshell.geom
import ezdxf
from bsa.source_network_drawing import project
from bsa.ifc_native import run as native
ROOT=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work')
RUN=ROOT/'runs/recentered-network-integrated'
DRAW=RUN/'drawing'
if DRAW.exists():raise ValueError('Fresh output required')
DRAW.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
audit=json.loads((RUN/'independent-native-review.json').read_text())
assert sha(RUN/'Supply Network.ifc')==audit['ifc_sha256']
assert audit['native_material_cap_pairs_matched']==88
clash=json.loads((RUN/'raw-clash/clash.json').read_text())
assert clash['valid_geometry_count']==89 and clash['intersection_pair_count']==0
ledger=json.loads((RUN/'pressure/maximum/pressure-ledger.json').read_text())
assert ledger['numerically_unresolved_fitting_path_count']==32
model=ifcopenshell.open(str(RUN/'Supply Network.ifc'));settings=ifcopenshell.geom.settings();settings.set(settings.USE_WORLD_COORDS,True)
items=[];all_vertices=[]
for obj in model.by_type('IfcDistributionElement'):
    shape=ifcopenshell.geom.create_shape(settings,obj)
    vertices=np.asarray(shape.geometry.verts).reshape(-1,3);faces=np.asarray(shape.geometry.faces).reshape(-1,3)
    items.append((obj.GlobalId,project(vertices,faces)));all_vertices.append(vertices)
vertices=np.vstack(all_vertices);lo=vertices.min(axis=0);hi=vertices.max(axis=0);span=hi-lo
scale=next(s for s in (200,250,300,400) if span[0]<=.27*s and span[1]<=.145*s)
offset=np.array([.01*scale,.025*scale])-lo[:2]
doc=ezdxf.new('R2018');doc.units=6;doc.appids.new('BSA_IFC');doc.layers.new('BSA_NETWORK_OUTLINE');doc.layers.new('BSA_SECTION_REFERENCE');msp=doc.modelspace();counts={}
for guid,polygons in items:
    counts[guid]=0
    for polygon in polygons:
        for ring in [polygon.exterior,*polygon.interiors]:
            points=np.asarray(ring.coords)[:-1]+offset
            entity=msp.add_lwpolyline(points.tolist(),close=True,dxfattribs={'layer':'BSA_NETWORK_OUTLINE'});entity.set_xdata('BSA_IFC',[(1000,guid)]);counts[guid]+=1
assert len(counts)==89 and all(counts.values())
def text(value,y,height=.0025):
    msp.add_text(value,dxfattribs={'height':height*scale,'insert':(.01*scale,y*scale)})
text('SUPPLY NETWORK COORDINATION STUDY',.188,.004)
text(f'Rigid network plan | scale 1:{scale} | not an installation drawing',.180)
text('89 bodies; 20 outlet paths; full pressure and clearance remain unverified',.012)
text('Recentered Connection Layout; hardware, installed clearance and fan duty unresolved',.005,.002)
ref=msp.add_line((.01*scale,.021*scale),(.01*scale+10,.021*scale),dxfattribs={'layer':'BSA_SECTION_REFERENCE'});ref.set_xdata('BSA_IFC',[(1000,items[0][0])])
msp.add_text('10 m reference',dxfattribs={'height':.0025*scale,'insert':(.01*scale+10+.005*scale,.020*scale)})
dxf=DRAW/'Supply Network Study.dxf';doc.saveas(dxf)
sheet=dict(source='Native saved IFC XY silhouettes; drawing translation only. Original nominal scale and reference elevation assumptions retained.',window_drawing_units=[0,0,.29*scale,.20*scale],scale_denominator=scale,reference_ifc_guid=items[0][0],reference_layer='BSA_SECTION_REFERENCE',drawing_name='section',pdf_tolerance_mm=.3)
(DRAW/'sheet-settings.json').write_text(json.dumps(sheet,indent=2))
result=native(dxf,DRAW/'sheet-settings.json',DRAW/'native')
(DRAW/'projection.json').write_text(json.dumps(dict(ifc_sha256=sha(RUN/'Supply Network.ifc'),dxf_sha256=sha(dxf),component_contour_counts=counts,drawing_translation_xy_m=offset.tolist(),all89native_guids_represented=True,native_reopen_pass=result['native_reopen_pass'],design_accepted=False),indent=2))
print(json.dumps(dict(ledger_outlets=ledger['outlet_count'],numerical_gaps=ledger['numerically_unresolved_fitting_path_count'],scale=scale,native_reopen_pass=result['native_reopen_pass']),indent=2))

"""Independent point arithmetic and native-derived local study drawing."""
import hashlib
import json
from decimal import Decimal as D
from pathlib import Path
import math
import numpy as np
import ifcopenshell
import ifcopenshell.geom
import ezdxf
from bsa.source_network_drawing import project
from bsa.ifc_native import run as native
from bsa import rectangular_tee as tee
from bsa.unequal_rectangular_tee import verify

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT/'runs/reduced-branch-design-final'
DRAW = RUN/'drawing-reviewed'
DRAW.mkdir(exist_ok=False)
record = json.loads((RUN/'study.json').read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert all(sha(Path(p)) == h for p,h in record['inputs'].items())
analysis = json.loads((ROOT/'runs/mcp-native-fitting-analysis/fitting-data.json').read_text())
selected = next(x for x in record['cases'] if x['revised_query']['coefficient'] is not None)
node = selected['node']; folder = RUN/node
assert node == 'TAP-VAV-04'
verify(folder/'native')
data = json.loads((folder/'project.json').read_text()); guid = tee.stable_guid(data['tee'],'IfcDuctFitting','RECTANGULAR-TEE')
old = next(x for x in analysis['data_requests'] if x['product_guid']==guid and x['recorded_table_result'] and x['recorded_table_result']['citation_location'].endswith('branch Cc,b'))
ports = {p['name']:p for p in old['available_reference_ports']}
incoming = next(p for p in ports.values() if p['direction']=='SINK')
flow = D(str(ports['branch']['flow_m3_s'])); main_flow = D(str(incoming['flow_m3_s']))
q = flow/main_flow; vr = (flow/(D('.35')*D('.30')))/(main_flow/(D('.60')*D('.40')))
# Four cells individually reviewed on original ASHRAE2021 printed42,5-28.
# v=.8/1.0, q=.3/.4. Values remain in this private project only.
u=(q-D('.3'))/D('.1'); v=(vr-D('.8'))/D('.2')
assert 0 <= u <= 1 and 0 <= v <= 1
lower=D('1.17')*(1-u)+D('1.12')*u
upper=D('1.30')*(1-u)+D('1.36')*u
k=lower*(1-v)+upper*v
velocity=main_flow/(D('.6')*D('.4')); vp=D('1.2')/2*velocity**2
loss=k*vp
assert math.isclose(float(k),selected['revised_query']['coefficient'],rel_tol=1e-12,abs_tol=0)
assert math.isclose(float(loss),selected['signed_conditional_loss_Pa'],rel_tol=1e-12,abs_tol=0)
checks=dict(source_page='ASHRAE2021 printed42,Fitting5-28',native_source_flow_recomputed=True,
    flow_ratio=float(q),velocity_ratio=float(vr),coefficient=float(k),conditional_loss_Pa=float(loss),
    independent_decimal_interpolation_matches=True,whole_fitting_pressure_verified=False,design_accepted=False)
(DRAW/'independent-point-check.json').write_text(json.dumps(checks,indent=2))
model = ifcopenshell.open(str(folder/'native/unequal-tee.ifc')); fitting=model.by_guid(guid)
settings=ifcopenshell.geom.settings();settings.set(settings.USE_WORLD_COORDS,True)
native_shape=ifcopenshell.geom.create_shape(settings,fitting)
mesh=native_shape.geometry
vertices=np.asarray(mesh.verts).reshape(-1,3);faces=np.asarray(mesh.faces).reshape(-1,3)
polygons=project(vertices,faces);lo=vertices.min(axis=0);translation=np.array([1.85, .45])-lo[:2]
doc=ezdxf.new('R2018');doc.units=6;doc.appids.new('BSA_IFC');doc.layers.new('BSA_SECTION_REFERENCE');doc.layers.new('BSA_OUTLINE');msp=doc.modelspace()
for polygon in polygons:
    for ring in [polygon.exterior,*polygon.interiors]:
        points=np.asarray(ring.coords)[:-1]+translation
        entity=msp.add_lwpolyline(points.tolist(),close=True,dxfattribs={'layer':'BSA_OUTLINE'});entity.set_xdata('BSA_IFC',[(1000,guid)])
def text(value,x,y,height=.025):
    msp.add_text(value,dxfattribs={'height':height,'insert':(x,y)})
text('BRANCH TEE DESIGN STUDY',.12,1.76,.04)
text('TAP-VAV-04 | plan | scale 1:10 | dimensions in metres',.12,1.66)
text('Main clear section: 0.600 x 0.400',.12,1.55)
text('Branch clear section: 0.350 x 0.300',.12,1.47)
text('Original external branch endpoint retained',.12,1.39)
text('Branch taper removed; main-arm transitions omitted from this view',.12,.27,.023)
text('LOCAL STUDY ONLY: no network pressure or installation acceptance',.12,.19,.023)
ref=msp.add_line((.12,.10),(1.12,.10),dxfattribs={'layer':'BSA_SECTION_REFERENCE'});ref.set_xdata('BSA_IFC',[(1000,guid)])
text('1 m reference',1.17,.09,.023)
source=DRAW/'Branch Tee Design Study.dxf';doc.saveas(source)
sheet=dict(source='Native IFC-derived local study. Drawing translation only; original model coordinates retained in IFC.',window_drawing_units=[0,0,2.8,1.9],scale_denominator=10,reference_ifc_guid=guid,reference_layer='BSA_SECTION_REFERENCE',drawing_name='section',pdf_tolerance_mm=.3)
(DRAW/'sheet-settings.json').write_text(json.dumps(sheet,indent=2))
receipt=native(source,DRAW/'sheet-settings.json',DRAW/'native-sheet')
(DRAW/'drawing-source.json').write_text(json.dumps(dict(ifc_sha256=sha(folder/'native/unequal-tee.ifc'),dxf_sha256=sha(source),translation_xy_m=translation.tolist(),native_reopen_pass=receipt['native_reopen_pass'],design_accepted=False),indent=2))
print(json.dumps(checks,indent=2));print('Native local sheet generated')

"""Project-specific composition of verified ledger and native drawing adapters."""
import hashlib
import html
import json
from pathlib import Path
import shutil
import numpy as np
import ifcopenshell
import ifcopenshell.geom
import ezdxf
from bsa.source_pressure_ledger import calculate
from bsa.source_network_drawing import project
from bsa.ifc_native import run as native

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'runs/reduced-branch-network-reviewed'
DRAW=RUN/'drawing'
if DRAW.exists():raise ValueError('Fresh drawing output required')
DRAW.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
audit=json.loads((RUN/'independent-review.json').read_text())
assert all(sha(RUN/p)==h for p,h in audit['artifact_sha256'].items())
case=json.loads((RUN/'analysis.json').read_text());loss=json.loads((RUN/'fitting-data.json').read_text())
loss['original_requirement_ids']=case['original_requirement_ids']
ledger=calculate(case,loss)
assert ledger['outlet_count']==20 and ledger['numerically_unresolved_fitting_path_count']==34
(RUN/'pressure-ledger.json').write_text(json.dumps(ledger,indent=2))
rows=[]
for row in ledger['outlet_paths']:
    port=case['port_flows'][row['outlet_port_guid']]
    rows.append('<tr>'+''.join('<td>'+html.escape(str(x))+'</td>' for x in [port['source_section'],f"{port['flow_m3_s']*1000:.3f}",f"{row['known_straight_friction_Pa']:.4f}",f"{row['conditional_signed_table_subtotal_Pa']:.4f}",len(row['numerically_unresolved_fitting_paths']),'Unknown'])+'</tr>')
report='''<!doctype html><html lang="en"><meta charset="utf-8"><title>Branch Network Pressure Study</title><style>body{font:16px/1.5 Arial;max-width:1100px;margin:30px auto;padding:20px;color:#23343e}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccd4d9;padding:8px;text-align:left}th{background:#eaf1f5}.pending{background:#fff0d2;padding:16px}</style><h1>Branch Network Pressure Study</h1><p class="pending">This is a separate source-linked study, not a complete fan pressure or accepted installation design. The original course plan and the Connection Layout scenario are preserved separately. Do not combine their geometry or sizes with this study.</p><p>Thirteen enlarged branch-plus-taper arrangements have been replaced by reduced-branch sharp tees, retaining original external end planes and prescribed flows. The saved model contains89bodies,197ports,88interfaces and20outlet paths. All88material cap pairs match. The same raw numerical policy finds no material intersection; clearance still fails at connected contacts. These are software controls, not installation clearances.</p><p>There are63fitting flow paths,29with conditional numerical source values and34without them. Removing13tapers removes3previously populated values and10unknown paths; one branch obtains a new bounded source value. No missing value becomes zero. Physical source applicability, whole-fitting friction/stations, adjacent-fitting interaction, flexible duct, terminal/equipment losses, boundary pressure and full coordination remain unresolved. The old branch loss was unknown, so no pressure saving is established.</p><h2>Separate outlet paths</h2><p>Conditional signed source subtotals are shown separately from native straight friction. They are not lower bounds or complete fan duties. Never sum parallel outlet paths.</p><table><tr><th>Outlet source section</th><th>Flow L/s</th><th>Known straight Pa</th><th>Conditional signed source subtotal Pa</th><th>Unknown fitting paths</th><th>Full path pressure</th></tr>'''+''.join(rows)+'''</table><h2>Basis and retained limitations</h2><p>Source:2021 ASHRAE Principles of HVAC Ninth Edition supplemental fitting tables, including5-28 for sharp rectangular branches. Only the original supported cells and exact native geometry conditions are used; there is no extrapolation. Nominal schedule dimensions are still assumed clear internal dimensions, gauge and elevation remain declared study assumptions. All33source requirements and six project input gaps remain. Actual room load and ADPI acceptance are not established by this pressure study.</p><p>The separate IFC and native drawing are review artifacts. Original source and private numerical provenance remain preserved in the selected project workspace.</p></html>'''
(RUN/'Branch Network Pressure Study.html').write_text(report,encoding='utf-8')
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
text('SUPPLY NETWORK DESIGN STUDY',.188,.004)
text(f'Rigid network plan | scale 1:{scale} | not an installation drawing',.180)
text('89 bodies; 20 outlet paths; full pressure and clearance remain unverified',.012)
text('Original source scenario; separate from the relocated VAV Connection Layout',.005,.002)
ref=msp.add_line((.01*scale,.021*scale),(.01*scale+10,.021*scale),dxfattribs={'layer':'BSA_SECTION_REFERENCE'});ref.set_xdata('BSA_IFC',[(1000,items[0][0])])
msp.add_text('10 m reference',dxfattribs={'height':.0025*scale,'insert':(.01*scale+10+.005*scale,.020*scale)})
dxf=DRAW/'Supply Network Study.dxf';doc.saveas(dxf)
sheet=dict(source='Native saved IFC XY silhouettes; drawing translation only. Original nominal scale and reference elevation assumptions retained.',window_drawing_units=[0,0,.29*scale,.20*scale],scale_denominator=scale,reference_ifc_guid=items[0][0],reference_layer='BSA_SECTION_REFERENCE',drawing_name='section',pdf_tolerance_mm=.3)
(DRAW/'sheet-settings.json').write_text(json.dumps(sheet,indent=2))
result=native(dxf,DRAW/'sheet-settings.json',DRAW/'native')
(DRAW/'projection.json').write_text(json.dumps(dict(ifc_sha256=sha(RUN/'Supply Network.ifc'),dxf_sha256=sha(dxf),component_contour_counts=counts,drawing_translation_xy_m=offset.tolist(),all89native_guids_represented=True,native_reopen_pass=result['native_reopen_pass'],design_accepted=False),indent=2))
print(json.dumps(dict(ledger_outlets=ledger['outlet_count'],numerical_gaps=ledger['numerically_unresolved_fitting_path_count'],scale=scale,native_reopen_pass=result['native_reopen_pass']),indent=2))

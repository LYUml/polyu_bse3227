"""Actual saved representative IFC longitudinal silhouettes, not a network plan."""
import hashlib,json
from pathlib import Path
import numpy as np
import ifcopenshell,ifcopenshell.geom as geom
import ezdxf,trimesh
from bsa.source_network_drawing import project
from bsa.circular_geometry import configure
from bsa.ifc_native import run as native

RUN=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/rect-round-cadquery/analytic-inlet-assemblies')
report=json.loads((RUN/'author-review.json').read_text());review=json.loads((RUN/'assembly-review.json').read_text())
IFC=RUN/'VAV Inlet Assemblies.ifc';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(IFC)==review['ifc_sha256']
OUT=RUN/'drawing-sections';OUT.mkdir(exist_ok=False)
model=ifcopenshell.open(str(IFC));settings=geom.settings();configure(settings)
doc=ezdxf.new('R2018');doc.units=6;doc.appids.new('BSA_IFC');msp=doc.modelspace()
for layer in ['BSA_INLET_OUTLINE','BSA_SECTION_REFERENCE']:doc.layers.new(layer)
represented=[];details=[]
for i,profile in enumerate(report['profiles']):
    rows=[r for r in report['cases'] if r['profile']==profile['profile']];row=rows[0]
    centre=.30+.56*i;offset=np.array([centre,.22+row['start_length_m']])
    counts={}
    for guid in [row['guid'],row['round_guid']]:
        obj=model.by_guid(guid);shape=geom.create_shape(settings,obj)
        vertices=np.array(shape.geometry.verts).reshape(-1,3);faces=np.array(shape.geometry.faces).reshape(-1,3)
        # World placements are excluded here; product-local axes establish a
        # longitudinal width/length view. Round lead local origin is translated
        # by the independently reviewed connected transition end station.
        coordinates=vertices[:,[0,2,1]]
        if guid==row['round_guid']:coordinates[:,1]+=row['taper_length_m']+row['end_length_m']
        mesh=trimesh.Trimesh(vertices=vertices,faces=faces,process=False)
        segments=trimesh.intersections.mesh_plane(mesh,[0,1,0],[0,0,0])
        assert len(segments)>0
        count=0
        for segment in segments:
            points=segment[:,[0,2]]
            if guid==row['round_guid']:points[:,1]+=row['taper_length_m']+row['end_length_m']
            points+=offset
            if np.linalg.norm(points[1]-points[0])<1e-10:continue
            entity=msp.add_line(tuple(points[0]),tuple(points[1]),dxfattribs={'layer':'BSA_INLET_OUTLINE'})
            entity.set_xdata('BSA_IFC',[(1000,guid)]);count+=1
        assert count>0;counts[guid]=count;represented.append(guid)
    msp.add_text(row['id']+' / '+str(len(rows))+' matching cases',dxfattribs={'height':.017,'insert':(centre-.23,1.75)})
    caption=f"{row['width_m']*1000:.0f}x{row['height_m']*1000:.0f} to D{row['diameter_m']*1000:.1f} mm"
    msp.add_text(caption,dxfattribs={'height':.016,'insert':(centre-.23,.13)})
    details.append(dict(representative=row['id'],matching_cases=[r['id'] for r in rows],contours=counts))
msp.add_text('VAV INLET CONNECTION SECTIONS',dxfattribs={'height':.04,'insert':(.07,1.92)})
msp.add_text('Saved IFC longitudinal material sections | scale1:10 | 0.3m taper and50mm collars are design assumptions',dxfattribs={'height':.018,'insert':(.07,1.84)})
msp.add_text('20 local assemblies; source duct replacement and actual product joints remain unverified',dxfattribs={'height':.018,'insert':(.07,.065)})
msp.add_text('Wall section offset0.8mm; no fabrication, full pressure, acoustics or installation acceptance',dxfattribs={'height':.018,'insert':(.07,.025)})
ref=msp.add_line((.10,.19),(.60,.19),dxfattribs={'layer':'BSA_SECTION_REFERENCE'});ref.set_xdata('BSA_IFC',[(1000,represented[0])])
msp.add_text('0.5m reference',dxfattribs={'height':.018,'insert':(.68,.183)})
dxf=OUT/'VAV Inlet Connections.dxf';doc.saveas(dxf)
sheet=dict(source='Actual saved native IFC longitudinal projection of representative source-bound20case families; separate placement assumptions remain in case records',
    window_drawing_units=[0,0,2.9,2.0],scale_denominator=10,reference_ifc_guid=represented[0],
    reference_layer='BSA_SECTION_REFERENCE',drawing_name='section',pdf_tolerance_mm=.3)
(OUT/'sheet.json').write_text(json.dumps(sheet,indent=2))
result=native(dxf,OUT/'sheet.json',OUT/'native')
(OUT/'projection.json').write_text(json.dumps(dict(ifc_sha256=sha(IFC),represented_GUIDs=represented,
    source_cases=20,representative_details=details,native_reopen_pass=result['native_reopen_pass'],
    visual_review='pending',design_accepted=False),indent=2))
print(json.dumps(dict(represented_native_GUIDs=len(represented),case_families=5,native_reopen_pass=result['native_reopen_pass'])))

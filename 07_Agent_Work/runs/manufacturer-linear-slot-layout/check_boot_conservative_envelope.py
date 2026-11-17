import json,hashlib
from pathlib import Path
from shapely.geometry import shape,box
base=Path(r'C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work');p=base/'runs/manufacturer-linear-slot-layout/boot-first-row-four-strip-services';a=json.loads((p/'allocation.json').read_text());r=json.loads((p/'All Boot Domain Combinations.json').read_text());b=shape(json.loads((base/'project/bse3227-column-row-candidate/office-boundary.geojson').read_text()));W={(.5,2):2.6875,(.5,4):5.1875,(.75,2):3.1875,(.75,4):6.1875,(1.,2):3.6875,(1.,4):7.1875};rows=[];envelopes=[]
for t,options in zip(a['terminals'],r['results']):
 widths=[]
 for key in options['source_domain_eligible']:
  opt=r['tables'][key];slotwidth=opt['slot_width_inch'];slots=opt['slots'];face=(1.5+slots*(slotwidth+.75))*.0254;plenum=W[(slotwidth,slots)]*.0254
  # Symmetric bounding envelope includes a 1 1/8in inlet projection on either side,
  # intentionally covering either inlet orientation without assigning an exact stub shape.
  widths.append(max(face,plenum+2*1.125*.0254))
 width=max(widths);length=48.75*.0254;x,y=t['center_m'];g=box(x-width/2,y-length/2,x+width/2,y+length/2);envelopes.append(g);rows.append(dict(id=t['id'],conservative_width_m=width,conservative_length_m=length,plenum_height_m=10.625*.0254,inside=b.covers(g)))
intersections=[(rows[i]['id'],rows[j]['id']) for i in range(len(rows)) for j in range(i) if envelopes[i].intersects(envelopes[j])];assert all(t['inside'] for t in rows) and not intersections
out=dict(scope='Conservative plan bounding envelope of all source-flow-eligible Frame B/plenum options, inlet projection on either side included; no exact oval stub shape, height placement or installation clearance acceptance',source_url='https://www.krueger-hvac.com/file/3272/1900BOOT_DimensionalData.pdf',source_sha256=hashlib.sha256((base/'project/adpi-manufacturer-study/linear-slot-source/1900 Boot Dimensional Data.pdf').read_bytes()).hexdigest(),frame_B_end_caps='assumed comparison configuration',rows=rows,inside_count=64,intersections=intersections,minimum_pairwise_envelope_gap_m=min(envelopes[i].distance(envelopes[j]) for i in range(len(rows)) for j in range(i)),vertical_placement_verified=False,design_accepted=False)
(p/'Boot Conservative Envelope Check.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='rows'}))

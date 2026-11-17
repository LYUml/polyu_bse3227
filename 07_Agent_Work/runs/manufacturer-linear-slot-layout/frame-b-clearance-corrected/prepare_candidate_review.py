import json,html,hashlib
from pathlib import Path
from collections import Counter
from fluids.numerics import interp
from shapely.geometry import shape
base=Path(r'C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work');p=base/'runs/manufacturer-linear-slot-layout/frame-b-clearance-corrected';a=json.loads((p/'allocation.json').read_text());r=json.loads((p/'slot-count-selection-33-samples.json').read_text());e=json.loads((p/'slot-count-event-sample-check.json').read_text());rows=[]
for index,(t,v,w) in enumerate(zip(a['terminals'],r['results'],e['results']),1):
 chosen=v['best']['slot_width_inch'];assert next(x for x in w['attempts'] if x['slot_width_inch']==chosen)['all_checks_pass'];table=r['tables'][chosen];data=table['rows'];cases={}
 for label,key in [('maximum','maximum_flow_L_s'),('minimum','minimum_flow_L_s')]:
  q=t[key]/1.2192;assert data[0]['flow_L_s_m']<=q<=data[-1]['flow_L_s_m'];cases[label]=dict(flow_L_s=t[key],flow_L_s_per_m=q,T050_m=interp(q,[z['flow_L_s_m'] for z in data],[z['T050_m'] for z in data]),diffuser_section_static_Pa=interp(q,[z['flow_L_s_m'] for z in data],[z['static_Pa'] for z in data]))
 rows.append(dict(plan_number=index,id=t['id'],center_m=t['center_m'],service_load_area_m2=t['allocated_load_area_m2'],selected=chosen,slot_width_inch=float(table['slot_width_inch']),slots=table['slots'],active_length_m=1.2192,source_page=table['pdf_page'],cases=cases,frame=None,outer_body_width_m=None,plenum=None,physical_ADPI_accepted=False))
package=dict(scope='Manufacturer comparison candidate, not coursework submission or accepted ADPI design',source_performance_sha256=r['performance_source_sha256'],flow_pressure_method='Linear interpolation in published per-length flow; section static pressure excludes plenum, not total pressure',selection_counts=dict(Counter(t['selected'] for t in rows)),terminals=rows,design_accepted=False)
(p/'Selected Linear Slot Schedule.json').write_text(json.dumps(package,indent=2))
# Inspectable vector plan; each service cell and active slot retains the same numbered identity.
boundary=shape(json.loads((base/'project/bse3227-column-row-candidate/office-boundary.geojson').read_text()));x0,y0,x1,y1=boundary.bounds;scale=23;ox=50;oy=805
X=lambda x:ox+(x-x0)*scale
Y=lambda y:oy-(y-y0)*scale
parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="930" viewBox="0 0 1200 930">','<rect width="1200" height="930" fill="white"/>','<text x="50" y="40" font-family="Arial" font-size="23">Manufacturer comparison: 63 linear-slot candidate</text>','<text x="50" y="66" font-family="Arial" font-size="14">Conditional paired-curve diagnostic only | 4 ft active slots | original coursework unchanged</text>']
def path(g):
 polygons=list(g.geoms) if hasattr(g,'geoms') else [g];out=[]
 for poly in polygons:
  if poly.geom_type != "Polygon":
   assert poly.area==0;continue
  for ring in [poly.exterior,*poly.interiors]:out.append('M '+' L '.join(f'{X(x):.3f},{Y(y):.3f}' for x,y in ring.coords)+' Z')
 return ' '.join(out)
for i,t in enumerate(a['terminals']):
 cell=shape(t['geometry']);color=['#e7eff9','#edf6e7','#fff0df'][i%3];parts.append(f'<path d="{path(cell)}" fill="{color}" stroke="#bac3cb" stroke-width="0.65" fill-rule="evenodd"/>')
parts.append(f'<path d="{path(boundary)}" fill="none" stroke="#222" stroke-width="1.8"/>')
for t in rows:
 x,y=t['center_m'];parts.append(f'<line x1="{X(x):.3f}" y1="{Y(y-.6096):.3f}" x2="{X(x):.3f}" y2="{Y(y+.6096):.3f}" stroke="#0755a4" stroke-width="3"/>');parts.append(f'<text x="{X(x)+6:.3f}" y="{Y(y)+3:.3f}" font-family="Arial" font-size="10">{t["plan_number"]}</text>')
parts+=['<text x="50" y="850" font-family="Arial" font-size="14">Blue = active slot centerline; coloured cells = assumed service areas; white voids = source columns.</text>','<text x="50" y="875" font-family="Arial" font-size="14">Outer frames, plenum bodies, heights and installation clearances remain unverified. Units: source metres.</text>','<text x="50" y="900" font-family="Arial" font-size="14">Numbers bind to Selected Linear Slot Schedule.json. Not a construction or submission drawing.</text>','</svg>'];(p/'Linear Slot Candidate Layout.svg').write_text('\n'.join(parts));print(json.dumps(dict(terminals=len(rows),selection_counts=package['selection_counts'])))

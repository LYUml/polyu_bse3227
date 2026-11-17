import json,hashlib,math
from pathlib import Path
import numpy as np,ifcopenshell
from ifcopenshell.util import placement,system
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs');R=B/'supported-transition-stages';O=B/'compound-source-feasibility';O.mkdir(exist_ok=False)
spec=json.loads((B/'source-compound-junction-native/junction-spec.json').read_text());f=ifcopenshell.open(str(R/'Supply Network.ifc'));o=f.by_guid('3tK$ugPAvIAAusb9mKjQEp');world=placement.get_local_placement(o.ObjectPlacement);assert np.allclose(world[:3,3],spec['placement']['origin_m'],atol=1e-10,rtol=0)
wall=o.Representation.Representations[0].Items[0];assert wall.Operator=='DIFFERENCE';cursor=wall.SecondOperand;branches=[]
while cursor.is_a('IfcBooleanResult'):
 assert cursor.Operator=='UNION';s=cursor.SecondOperand;branches.append(s);cursor=cursor.FirstOperand
assert cursor.is_a('IfcFacetedBrep');pts=np.unique(np.array([p.Coordinates for face in cursor.Outer.CfsFaces for p in face.Bounds[0].Bound.Polygon]),axis=0);stations=[]
for y in sorted(set(pts[:,1])):
 row=pts[pts[:,1]==y];assert len(row)==4;stations.append(dict(y_m=float(y),width_m=float(np.ptp(row[:,0])),height_m=float(np.ptp(row[:,2]))))
assert stations==spec['stations']
for s,b in zip(reversed(branches),spec['branches']):
 assert np.allclose([s.SweptArea.XDim,s.SweptArea.YDim,s.Depth],[b['width_m'],b['height_m'],b['reach_m']],rtol=0,atol=1e-12)
 assert np.allclose(placement.get_axis2placement(s.Position)[:3,3],[0,b['y_m'],0],rtol=0,atol=1e-12)
rows=[]
for b in spec['branches']:
 lo=b['y_m']-b['width_m']/2;hi=b['y_m']+b['width_m']/2;over=[]
 for a,c in zip(stations,stations[1:]):
  l=max(lo,a['y_m']);h=min(hi,c['y_m'])
  if h>l and (a['width_m']!=c['width_m'] or a['height_m']!=c['height_m']):over.append(dict(interval_m=[l,h],length_m=h-l))
 rows.append(dict(branch=b['id'],aperture_interval_m=[lo,hi],taper_overlaps=over,independent_constant_section_junction_supported=not over))
assert all(r['taper_overlaps'] for r in rows)
flows=json.loads((R/'flow-review.json').read_text())['cases'];ports=system.get_ports(o);cases={}
for name,case in flows.items():
 q={p.Name:case['port_flows'][p.GlobalId]['flow_m3_s'] for p in ports};assert math.isclose(q['upper'],sum(v for k,v in q.items() if k!='upper'),rel_tol=1e-12);cases[name]=dict(external_flows_m3_s=q,after_upper_takeoff_m3_s=q['upper']-q['D-22'],after_lower_takeoffs_m3_s=q['lower'])
upper=next(r for r in rows if r['branch']=='D-22');lower=[r for r in rows if r['branch']!='D-22'];gap=upper['aperture_interval_m'][0]-max(r['aperture_interval_m'][1] for r in lower)
report=dict(ifc_sha256=hashlib.sha256((R/'Supply Network.ifc').read_bytes()).hexdigest(),product_guid=o.GlobalId,native_inner_stations=stations,native_branch_dimensions_match=True,branches=rows,clear_trunk_between_apertures_m=gap,cases=cases,independent_fitting_decomposition_accepted=False,reason='All three native branch apertures intersect varying-section trunk regions. Constant-section tee/cross plus isolated taper coefficients cannot be assigned to unchanged body.',full_pressure_accepted=False,next_design='Separate constant-section source-family junction cores from transitions; preserve five external caps and solve finite available reach, height correspondence and close-coupling explicitly.')
(O/'review.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))

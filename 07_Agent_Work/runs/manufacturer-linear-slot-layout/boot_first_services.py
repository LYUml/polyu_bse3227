import json,hashlib,copy
from pathlib import Path
from shapely.geometry import shape,box,mapping,Point
from shapely import union_all
base=Path(r'C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work');runs=base/'runs/manufacturer-linear-slot-layout';source=base/'project/bse3227-column-row-candidate/office-boundary.geojson';assert hashlib.sha256(source.read_bytes()).hexdigest()=='c64f5b2df5be607b7aebc978a51d3a168b45ca9e057135f0df6540e651a4a617';boundary=shape(json.loads(source.read_text()))
for oldname in ['boot-first-row-four']:
 old=runs/oldname;out=runs/(oldname+'-strip-services');out.mkdir(exist_ok=True);a=json.loads((old/'allocation.json').read_text());fresh=copy.deepcopy(a);cells={}
 for zone,lo,hi in [('main',16.105584,36.595584),('bay',36.595584,45.725584)]:
  points=[t for t in a['terminals'] if (t['id'].startswith('bay-'))==(zone=='bay')];ys=sorted(set(t['center_m'][1] for t in points));cuts=[lo]+[(ys[i]+ys[i+1])/2 for i in range(len(ys)-1)]+[hi]
  if zone=='main':cuts[1]=18.25
  for i,y in enumerate(ys):
   row=sorted([t for t in points if t['center_m'][1]==y],key=lambda t:t['center_m'][0]);xs=[t['center_m'][0] for t in row];xcuts=[64.525932]+[(xs[j]+xs[j+1])/2 for j in range(len(xs)-1)]+[109.165932]
   for j,t in enumerate(row):
    cell=boundary.intersection(box(xcuts[j],cuts[i],xcuts[j+1],cuts[i+1]));assert not cell.is_empty and cell.covers(Point(t['center_m']));cells[t['id']]=cell
 union=union_all(list(cells.values()));assert boundary.symmetric_difference(union).area<1e-8;assert abs(sum(c.area for c in cells.values())-union.area)<1e-8
 for t in fresh['terminals']:
  cell=cells[t['id']];t['geometry']=mapping(cell);t['geometric_area_m2']=cell.area;t['allocated_load_area_m2']=cell.area/boundary.area*1022;t['maximum_flow_L_s']=cell.area/boundary.area*a['load']['supply_flow_L_s'];t['minimum_flow_L_s']=t['maximum_flow_L_s']*.4
 fresh['allocation']['terminals']=[{k:t[k] for k in ['id','center_m','geometry','geometric_area_m2','allocated_load_area_m2']} for t in fresh['terminals']];fresh['scope']='Explicit source-clipped row/column service-strip design assumption, not measured room load or proven air coverage';fresh['checks'].update(allocated_area_m2=sum(t['allocated_load_area_m2'] for t in fresh['terminals']),allocated_flow_L_s=sum(t['maximum_flow_L_s'] for t in fresh['terminals']));assert abs(fresh['checks']['allocated_flow_L_s']-a['load']['supply_flow_L_s'])<1e-8
 (out/'allocation.json').write_text(json.dumps(fresh,indent=2));(out/'service-partition-check.json').write_text(json.dumps(dict(scope=fresh['scope'],source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),symmetric_difference_m2=boundary.symmetric_difference(union).area,overlap_area_m2=sum(c.area for c in cells.values())-union.area,center_in_assigned_service_cells=True,checks=fresh['checks']),indent=2))
 for name in ['first-candidate.json','independent-performance-check.json']:(out/name).write_bytes((old/name).read_bytes())
 for name in ['check_finite_slots.py','check_dense_samples.py']:(out/name).write_text((old/name).read_text().replace(f'manufacturer-linear-slot-layout/{oldname}',f'manufacturer-linear-slot-layout/{oldname}-strip-services'))
 print(out.name,len(cells),fresh['checks'])

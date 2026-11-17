import json,re,hashlib,copy,collections,csv
from pathlib import Path
import numpy as np,ifcopenshell
from ifcopenshell.util import system
from bsa.cli import digest
R=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work');base=R/'runs/general-drawing-current-open-plenum-plan';source=R/'runs/recentered-open-plenum-network/Supply Air Open Plenum Reviewed.ifc';m=ifcopenshell.open(str(source));binding=json.loads((base/'section-result.json').read_text())['source'];assert digest(source)==binding['ifc_sha256'];d=json.loads((base/'layout/resolved-document.json').read_text());assert not d['blocks'];grouped=collections.defaultdict(list);retained=[]
for e in d['entities']:
 match=re.search(r'[0-3][A-Za-z0-9_$]{21}',e['id'])
 if e['kind']=='polyline' and match:grouped[match.group()].append(e)
 else:retained.append(e)
SHIFT=np.array([2500.,12000.])
for e in retained:
 if e['kind']=='text':e['insert']=(np.asarray(e['insert'])+SHIFT).tolist()
d['sheet'].update(paper='A1',window=[0,0,83000,58000],scale=100)
assert set(grouped)=={o.GlobalId for o in m.by_type('IfcDistributionElement')};inserts={}
for guid,entities in sorted(grouped.items()):
 points=np.asarray([p for e in entities for p in e['points']]);centre=(points.min(axis=0)+points.max(axis=0))/2;name='IFC_'+guid;items=copy.deepcopy(entities)
 for e in items:e['points']=(np.asarray(e['points'])-centre).tolist()
 d['blocks'][name]=items;insert=dict(id='product:'+guid,kind='insert',layer='MATERIAL',source='Source-bound native IFC projection '+digest(source)+'; '+guid,classification='secondary_transcription',block=name,insert=(centre+SHIFT).tolist(),rotation=0,scale=1);retained.append(insert);inserts[guid]=insert
assert len(set(n.upper() for n in d['blocks']))==598
d['entities']=retained;d['layers']['IDENTIFIERS']=dict(color=7,lineweight=18);d['layers']['TAG_LEADERS']=dict(color=8,lineweight=9)
I=json.loads((R/'runs/logical-equipment-network/integration.json').read_text());flow=json.loads((R/'runs/recentered-logical-supply-network/flow-review.json').read_text())['cases']['maximum'];mapping=[]
for r in I['records']:mapping.append(dict(label=r['id'],product_guid=r['vav_guid'],native_port_guid=r['vav_inlet_guid'],role='candidate VAV envelope'))
for g in flow['boundary_outlet_guids']:
 owner=system.get_port_element(m.by_guid(g));label=flow['port_flows'][g]['source_section'];assert owner.Name==label+'/terminal-bend';mapping.append(dict(label=label,product_guid=owner.GlobalId,native_port_guid=g,role='terminal connection plane'))
assert len(mapping)==100 and len({r['label'] for r in mapping})==100
labels=[]
for r in mapping:
 e=inserts[r['product_guid']];ident='tag:'+r['label'];d['entities'].append(dict(id=ident,kind='text',layer='IDENTIFIERS',source='Native IFC '+digest(source)+'; '+r['product_guid']+'; '+r['native_port_guid']+'; '+r['role'],classification='secondary_transcription',insert=e['insert'],text=r['label'],height=250,rotation=0));labels.append(dict(id=ident,target=e['id']));r.update(label_id=ident,target_insert_id=e['id'])
d['layers']['SCHEDULE']=dict(color=7,lineweight=13)
station=R/'runs/recentered-logical-supply-network/vav-candidate-station-pressure/VAV Candidate Station Pressure.csv'
with station.open(newline='',encoding='utf-8') as f:rows=list(csv.DictReader(f))
by={(r['vav'],r['condition']):r for r in rows};xs=[50000]
for width in [4000,4500,4500,5500,5500,4000]:xs.append(xs[-1]+width)
ytop=44000;row_height=700;source_text='Calculated source flow and fully-open station comparison CSV SHA256 '+digest(station)
def text(ident,string,x,y,height=300):d['entities'].append(dict(id=ident,kind='text',layer='SCHEDULE',source=source_text,classification='secondary_transcription',insert=[float(x),float(y)],text=string,height=height,rotation=0))
def line(ident,a,b):d['entities'].append(dict(id=ident,kind='line',layer='SCHEDULE',source='Host graphic table grid',classification='assumed',start=a,end=b))
text('schedule-title','CONDITIONAL VAV STATION COMPARISON',xs[0],ytop+1000,400)
headers=['VAV','Max L/s','Min L/s','Open Pt max Pa','Open Pt min Pa','Nominal in']
for j,h in enumerate(headers):text('schedule-header-'+str(j),h,xs[j]+300,ytop-500)
for i,g in enumerate(sorted(r['id'] for r in I['records'])):
 maximum,minimum=by[(g,'maximum')],by[(g,'minimum')];values=[g,format(float(maximum['design_flow_m3_s'])*1000,'.2f'),format(float(minimum['design_flow_m3_s'])*1000,'.2f'),format(float(maximum['conditional_total_difference_Pa']),'.2f'),format(float(minimum['conditional_total_difference_Pa']),'.2f'),maximum['nominal_inlet_in']]
 for j,v in enumerate(values):text('schedule-'+g+'-'+str(j),v,xs[j]+300,ytop-(i+1)*row_height-500)
for i in range(22):line('schedule-horizontal-'+str(i),[xs[0],ytop-i*row_height],[xs[-1],ytop-i*row_height])
for i,x in enumerate(xs):line('schedule-vertical-'+str(i),[x,ytop],[x,ytop-21*row_height])
for i,string in enumerate(['Basis: Krueger LMHS2021 A2-26/27; full-open static curve.', 'Pt = Ps + inlet velocity pressure - discharge velocity pressure.', 'Reference stations and density assumed; controlled VAV loss unknown.', 'VAV tags: candidate envelopes; SD tags: terminal connection planes.']):text('schedule-note-'+str(i),string,xs[0],ytop-21*row_height-800-i*450,250)
spec=dict(schema='bsa.drawing-labels/1',source='Current candidate IFC '+digest(source)+'; base projected document '+digest(base/'layout/resolved-document.json')+'; labels identify source-owned VAVs and terminal connections',document=d,labels=labels,avoid=[e['id'] for e in inserts.values()],bounds=[800,2600,48000,56200],gap_mm=.5,min_distance_mm=3,max_distance_mm=15,candidates=400,leader_layer='TAG_LEADERS')
p=R/'project/general-drawing/current-open-plenum-tags-a1.json';p.write_text(json.dumps(spec,indent=2)+'\n',encoding='utf-8');(R/'project/general-drawing/current-open-plenum-tag-binding-a1.json').write_text(json.dumps(dict(ifc_sha256=digest(source),base_document_sha256=digest(base/'layout/resolved-document.json'),drawing_only_translation_mm=SHIFT.tolist(),block_products=598,material_contours=sum(map(len,grouped.values())),labels=mapping),indent=2)+'\n',encoding='utf-8');print('598blocks/100source-mappedlabels prepared',flush=True)

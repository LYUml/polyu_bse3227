import json,re,hashlib,copy,collections
from pathlib import Path
import numpy as np,ifcopenshell
from ifcopenshell.util import system
from bsa.cli import digest
R=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work');base=R/'runs/general-drawing-current-open-plenum-plan';source=R/'runs/recentered-open-plenum-network/Supply Air Open Plenum Reviewed.ifc';m=ifcopenshell.open(str(source));binding=json.loads((base/'section-result.json').read_text())['source'];assert digest(source)==binding['ifc_sha256'];d=json.loads((base/'layout/resolved-document.json').read_text());assert not d['blocks'];grouped=collections.defaultdict(list);retained=[]
for e in d['entities']:
 match=re.search(r'[0-3][A-Za-z0-9_$]{21}',e['id'])
 if e['kind']=='polyline' and match:grouped[match.group()].append(e)
 else:retained.append(e)
assert set(grouped)=={o.GlobalId for o in m.by_type('IfcDistributionElement')};inserts={}
for guid,entities in sorted(grouped.items()):
 points=np.asarray([p for e in entities for p in e['points']]);centre=(points.min(axis=0)+points.max(axis=0))/2;name='IFC_'+guid;items=copy.deepcopy(entities)
 for e in items:e['points']=(np.asarray(e['points'])-centre).tolist()
 d['blocks'][name]=items;insert=dict(id='product:'+guid,kind='insert',layer='MATERIAL',source='Source-bound native IFC projection '+digest(source)+'; '+guid,classification='secondary_transcription',block=name,insert=centre.tolist(),rotation=0,scale=1);retained.append(insert);inserts[guid]=insert
assert len(set(n.upper() for n in d['blocks']))==598
d['entities']=retained;d['layers']['IDENTIFIERS']=dict(color=7,lineweight=18);d['layers']['TAG_LEADERS']=dict(color=8,lineweight=9)
I=json.loads((R/'runs/logical-equipment-network/integration.json').read_text());flow=json.loads((R/'runs/recentered-logical-supply-network/flow-review.json').read_text())['cases']['maximum'];mapping=[]
for r in I['records']:mapping.append(dict(label=r['id'],product_guid=r['vav_guid'],native_port_guid=r['vav_inlet_guid'],role='candidate VAV envelope'))
for g in flow['boundary_outlet_guids']:
 owner=system.get_port_element(m.by_guid(g));label=flow['port_flows'][g]['source_section'];assert owner.Name==label+'/terminal-bend';mapping.append(dict(label=label,product_guid=owner.GlobalId,native_port_guid=g,role='terminal connection plane'))
assert len(mapping)==100 and len({r['label'] for r in mapping})==100
labels=[]
for r in mapping:
 e=inserts[r['product_guid']];ident='tag:'+r['label'];d['entities'].append(dict(id=ident,kind='text',layer='IDENTIFIERS',source='Native IFC '+digest(source)+'; '+r['product_guid']+'; '+r['native_port_guid']+'; '+r['role'],classification='secondary_transcription',insert=e['insert'],text=r['label'],height=500,rotation=0));labels.append(dict(id=ident,target=e['id']));r.update(label_id=ident,target_insert_id=e['id'])
spec=dict(schema='bsa.drawing-labels/1',source='Current candidate IFC '+digest(source)+'; base projected document '+digest(base/'layout/resolved-document.json')+'; labels identify source-owned VAVs and terminal connections',document=d,labels=labels,avoid=[e['id'] for e in inserts.values()],bounds=[1600,5200,56400,36400],gap_mm=.5,min_distance_mm=3,max_distance_mm=15,candidates=400,leader_layer='TAG_LEADERS')
p=R/'project/general-drawing/current-open-plenum-tags.json';p.write_text(json.dumps(spec,indent=2)+'\n',encoding='utf-8');(R/'project/general-drawing/current-open-plenum-tag-binding.json').write_text(json.dumps(dict(ifc_sha256=digest(source),base_document_sha256=digest(base/'layout/resolved-document.json'),block_products=598,material_contours=sum(map(len,grouped.values())),labels=mapping),indent=2)+'\n',encoding='utf-8');print('598blocks/100source-mappedlabels prepared',flush=True)

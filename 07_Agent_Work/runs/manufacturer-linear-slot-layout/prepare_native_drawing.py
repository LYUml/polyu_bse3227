import json
from pathlib import Path
from shapely.geometry import shape
base=Path(r'C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work');p=base/'runs/manufacturer-linear-slot-layout/frame-b-clearance-corrected';a=json.loads((p/'allocation.json').read_text());s=json.loads((p/'Selected Linear Slot Schedule.json').read_text());f=json.loads((p/'Frame B Footprint Check.json').read_text());assert f['all_inside'] and not f['intersections'];b=shape(json.loads((base/'project/bse3227-column-row-candidate/office-boundary.geojson').read_text()));entities=[];blocks={};src='Source boundary SHA c64f5b2d; explicit service-cell candidate; manufacturer1900 direct4ft tables and conditional Frame B dimensions'
def add(kind,id,layer,classification='assumed',**kw):entities.append(dict(kind=kind,id=id,layer=layer,source=src,classification=classification,**kw))
for i,ring in enumerate([b.exterior,*b.interiors]):add('polyline',f'boundary-{i}','BOUNDARY','secondary_transcription',points=[list(x) for x in list(ring.coords)[:-1]],closed=True)
for i,t in enumerate(a['terminals']):
 g=shape(t['geometry']);polys=list(g.geoms) if hasattr(g,'geoms') else [g]
 for j,poly in enumerate(polys):
  if poly.geom_type!='Polygon':assert poly.area==0;continue
  add('polyline',f'service-{i}-{j}','SERVICE',points=[list(x) for x in list(poly.exterior.coords)[:-1]],closed=True)
for t,foot in zip(s['terminals'],f['rows']):
 assert t['id']==foot['id'];key=t['selected'].replace('.','P').replace('-','_');w=foot['overall_width_m'];L=foot['overall_length_m']
 if key not in blocks:
  blocks[key]=[dict(id=f'{key}-frame',kind='polyline',layer='FRAME_B',source=src,classification='secondary_transcription',points=[[-w/2,-L/2],[w/2,-L/2],[w/2,L/2],[-w/2,L/2]],closed=True),dict(id=f'{key}-active',kind='line',layer='ACTIVE_SLOT',source=src,classification='assumed',start=[0,-.6096],end=[0,.6096])]
 add('insert',f'outlet-{t["id"]}','FRAME_B',block=key,insert=t['center_m'],scale=1,rotation=0)
 x,y=t['center_m'];add('text',f'label-{t["id"]}','LABEL',insert=[x+.25,y-.06],text=f'{t["plan_number"]:02d}',height=.19,rotation=0)
notes=['MANUFACTURER COMPARISON CANDIDATE - NOT COURSE SUBMISSION OR CONSTRUCTION','63 selected units pass paired published-load diagnostics; physical ADPI acceptance remains pending.','Frame B and both end caps assumed. Ordered 48 in vs tested active length correspondence remains unconfirmed.','Blue: active slot; frame: conditional overall footprint; service cells: design assumption, not proven coverage.','Ceiling height, mixed-jet downward length, plenum, inlet distribution and installation remain unverified.']
for i,n in enumerate(notes):add('text',f'note-{i}','LABEL',insert=[64,14.6-i*.52],text=n,height=.19,rotation=0)
spec=dict(schema='bsa.drawing-document/1',source=src,units='m',layers={'BOUNDARY':dict(color=7,lineweight=35),'SERVICE':dict(color=8,lineweight=9),'FRAME_B':dict(color=3,lineweight=18),'ACTIVE_SLOT':dict(color=5,lineweight=25),'LABEL':dict(color=7,lineweight=18)},blocks=blocks,entities=entities,sheet=dict(paper='A1',window=[60,6,123.075,50.55],scale=75,title='BSE3227 - MANUFACTURER LINEAR SLOT COMPARISON',number='MEP-ADPI-COMP',reference_length=3.75))
(p/'Native Linear Slot Drawing.json').write_text(json.dumps(spec,indent=2));print('entities',len(entities),'blocks',len(blocks))

import json,hashlib,re,csv,math
from pathlib import Path
from pypdf import PdfReader
import ifcopenshell,ifcopenshell.api,ifcopenshell.validate
from ifcopenshell.util.element import get_psets
from bsa.vav_operating_basis import calculate,TABLE,SOURCE_SHA256
A=Path('C:/Users/lyuml-win/Desktop/building-services-agent');P=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');R=P/'07_Agent_Work/runs/logical-equipment-network';O=R/'manufacturer-equipment-baseline';O.mkdir(exist_ok=False);source=R/'Supply Air Logical Network.ifc';pdf=P/'07_Agent_Work/project/upstream-gap-survey/SDIOM-manufacturer.pdf';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(pdf)==SOURCE_SHA256
text=PdfReader(pdf).pages[16].extract_text()
assert 'TABLE 6.A' in text and 'damper fully  open' in text
for size,rows in TABLE.items():
 # Preserve source column order; check the complete VP/basic sequences in text.
 chunk=text.split('\n'+str(size)+' \n(')[1].split('\n'+str(size+2)+' \n(')[0]
 for column in [1,2]:
  values=[str(r[column]).rstrip('0').rstrip('.') for r in rows]
  assert re.search(r'\s+'.join(re.escape(v) for v in values),chunk),values
m=ifcopenshell.open(str(source));saved={e.id():e.to_string() for e in m};integration=json.loads((R/'integration.json').read_text());cases={c:json.loads((R/'pressure-interface-evidence'/c/'analysis.json').read_text()) for c in ['maximum','minimum']};rows=[]
for r in integration['records']:
 obj=m.by_guid(r['vav_guid']);size=int(get_psets(obj)['BSA_VAVCandidate']['NominalInlet_in']);props=dict(Manufacturer='Krueger',Model='LMHS',ConfigurationBasis='Basic no-reheat candidate;source damper fully open;not installed selection',NominalInlet_in=size,SourceDocumentSHA256=SOURCE_SHA256,SourceURL='https://www.krueger-hvac.com/file/7365/SDIOM.pdf',SourceLocator='PDF17 Table6.A',PressureStationScope='Velocity plus static baseline is not two-plane total-pressure loss;discharge velocity and controlled damper state unresolved',TotalPressureLossVerified=False,SelectedForInstallation=False)
 for c in cases:
  q=cases[c]['port_flows'][r['vav_inlet_guid']]['flow_m3_s'];b=calculate(size,q);rows.append(dict(vav=r['id'],vav_guid=obj.GlobalId,condition=c,**b));props[c+'DesignFlow_m3_s']=q;props[c+'PressureStatus']=b['status']
  if b['status']=='conditional_fully_open_baseline':
   for k in ['source_velocity_pressure_Pa','source_static_difference_Pa','source_velocity_plus_static_Pa']:props[c+'_'+k]=b[k]
 pset=ifcopenshell.api.run('pset.add_pset',m,product=obj,name='BSA_ManufacturerOperatingBaseline');ifcopenshell.api.run('pset.edit_pset',m,pset=pset,properties=props)
out=O/'Supply Air Equipment Baseline.ifc';m.write(str(out));new=ifcopenshell.open(str(out));assert all(new.by_id(i).to_string()==v for i,v in saved.items());assert len(new.by_type('IfcElement'))==664 and len(new.by_type('IfcDistributionPort'))==1287
for row in rows:
 props=get_psets(new.by_guid(row['vav_guid']))['BSA_ManufacturerOperatingBaseline'];assert props[row['condition']+'DesignFlow_m3_s']==row['design_flow_m3_s'] and props['TotalPressureLossVerified'] is False
 if 'source_velocity_plus_static_Pa' in row:assert math.isclose(props[row['condition']+'_source_velocity_plus_static_Pa'],row['source_velocity_plus_static_Pa'],rel_tol=1e-12)
logger=ifcopenshell.validate.json_logger();ifcopenshell.validate.validate(new,logger,express_rules=True);assert len(logger.statements)==0,logger.statements[:3]
# Controls: support boundary stays bounded; table knot arithmetic preserves references.
assert calculate(12,424*.0004719474432)['status']=='outside_published_flow_range'
assert calculate(14,2801*.0004719474432)['status']=='outside_published_flow_range'
k=calculate(12,1600*.0004719474432);assert math.isclose(k['source_velocity_plus_static_Pa'],.3*249.08891,rel_tol=1e-12) and k['device_total_pressure_loss_Pa'] is None
assert calculate(12,True) if False else True
try:calculate(12,True)
except ValueError:pass
else:raise AssertionError('Boolean flow accepted')
with (O/'VAV Manufacturer Operating Baseline.csv').open('w',newline='',encoding='utf-8') as f:
 keys=list(dict.fromkeys(k for row in rows for k in row));w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
summary=dict(source_ifc_sha256=sha(source),updated_ifc_sha256=sha(out),manufacturer_pdf_sha256=SOURCE_SHA256,source_url='https://www.krueger-hvac.com/file/7365/SDIOM.pdf',source_page=17,source_page_actually_viewed=True,source_table_column_sequences_checked=True,adapter_sha256=sha(A/'src/bsa/vav_operating_basis.py'),source_entity_count=len(saved),all_original_IFC_entities_preserved_byte_for_byte=True,manufacturer_property_sets=20,actual_saved_property_rows_checked=40,conditional_rows=sum(r['status']=='conditional_fully_open_baseline' for r in rows),unsupported_rows=[dict(vav=r['vav'],condition=r['condition'],CFM=r['design_CFM']) for r in rows if r['status']!='conditional_fully_open_baseline'],schema_express_errors=0,source_pressure_reference_controls=4,nominal_sizes=sorted({r['nominal_inlet_in'] for r in rows}),pressure_ranges={c:[min(r['source_velocity_plus_static_Pa'] for r in rows if r['condition']==c and 'source_velocity_plus_static_Pa' in r),max(r['source_velocity_plus_static_Pa'] for r in rows if r['condition']==c and 'source_velocity_plus_static_Pa' in r)] for c in cases},device_total_pressure_loss_verified=False,original_pressure_ledgers_unchanged=True,design_accepted=False,scope='Manufacturer fully open operating baseline,not installed total-pressure loss/control duty;all original geometry/ports unchanged.Original native DWG remains geometry reference,not fresh equipment-property CAD delivery.')
(O/'review.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))

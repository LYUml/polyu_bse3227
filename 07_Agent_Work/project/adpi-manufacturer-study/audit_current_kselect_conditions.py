from pathlib import Path
import json,csv,hashlib,math
from decimal import Decimal,localcontext
from bsa.manufacturer_adpi import catalogue
P=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');B=P/'07_Agent_Work/runs';W=B/'current-course-kselect-all-conditions';O=B/'current-course-kselect-review';O.mkdir(exist_ok=False)
read=lambda p:json.loads(p.read_text(encoding='utf-8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
batch=read(W/'batch-complete.json');independent=read(W/'independent-native-report-check.json');native={r['effective_cfm']:r for r in independent['records']}
source=P/'05_Calculations/Connection_Layout/Diffuser Course Ratio Check.csv';rows=list(csv.DictReader(source.open()))
comparison=read(B/'manufacturer-adpi-comparison/comparison.json');table=catalogue(Path(comparison['performance_pdf']))['8'];results=[];requests={}
def linear(q,key):
 for a,b in zip(table,table[1:]):
  x,y=Decimal(str(a['flow_L_s'])),Decimal(str(b['flow_L_s']))
  if x<=q<=y:return Decimal(str(a[key]))+(Decimal(str(b[key]))-Decimal(str(a[key])))*(q-x)/(y-x)
 raise AssertionError('Outside original source table')
with localcontext() as ctx:
 ctx.prec=40
 for row in rows:
  q=Decimal(row['flow_L_s']);cfm=int((q*Decimal('2.118880003289315')+Decimal('.5')).to_integral_value(rounding='ROUND_FLOOR'))
  n=native[cfm];selected=n['native_selected'];T=Decimal(str(selected['throw_ft']))*Decimal('.3048');L=Decimal(row['L_m']);ratio=T/L
  effective=Decimal(cfm)/Decimal('2.118880003289315');historical=linear(q,'T025_m');at_effective=linear(effective,'T025_m')
  assert abs(historical-Decimal(row['T025_m']))<Decimal('2e-14')
  record={**{k:row[k] for k in ['terminal','direction','case','flow_L_s','L_m']},'effective_cfm':cfm,'effective_flow_L_s':str(effective),'native_reported_throw_ft':str(selected['throw_ft']),'native_T025_m':str(T),'native_ratio':str(ratio),'classroom_interval_met':Decimal(1)<=ratio<=Decimal('3.4'),'original_catalogue_T025_m':str(historical),'original_catalogue_ratio':row['ratio'],'catalogue_T025_at_effective_flow_m':str(at_effective),'native_minus_catalogue_T025_at_effective_flow_m':str(T-at_effective),'native_pdf_sha256':n['pdf_sha256']}
  results.append(record)
  requests[(row['terminal'],row['case'])]=record
 assert len(results)==640 and len(requests)==160 and len(native)==49
 for case in ['maximum','minimum']:
  ids={r['terminal'] for r in results if r['case']==case};assert len(ids)==80
with (O/'Native K-Select Ratio Check.csv').open('w',encoding='utf-8-sig',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=list(results[0]));writer.writeheader();writer.writerows(results)
lo=min(results,key=lambda r:Decimal(r['native_ratio']));hi=max(results,key=lambda r:Decimal(r['native_ratio']))
summary={'scope':'Actual current-course Model1400/24x24/8inch/F23 horizontal50fpm native GRD verification; old catalogue coursework calculation retained separately','toolkit_HEAD':'3eecd3710e976927c4b7c639900e833d12150453','toolkit_version':'0.1.1','native_backend':'Krueger GRD10.0.2','native_conditions':49,'new_native_executions':49,'within_batch_new_executions':47,'within_batch_reused_critical_reports':2,'terminal_operating_cases':160,'directional_operating_checks':640,'all640_reported_native_ratios_within_classroom_interval':all(r['classroom_interval_met'] for r in results),'native_ratio_minimum':float(lo['native_ratio']),'native_ratio_maximum':float(hi['native_ratio']),'minimum_case':lo,'maximum_case':hi,'maximum_absolute_input_rounding_L_s':max(abs(float(r['effective_flow_L_s'])-float(r['flow_L_s'])) for r in results),'maximum_absolute_throw_difference_at_equal_effective_flow_m':max(abs(float(r['native_minus_catalogue_T025_at_effective_flow_m'])) for r in results),'independent_native_pdf_check':{k:v for k,v in independent.items() if k!='records'},'all640_catalogue_interpolations_independently_reconciled_by_Decimal':True,'source_ratio_csv_sha256':sha(source),'native_ratio_csv_sha256':sha(O/'Native K-Select Ratio Check.csv'),'performance_source_sha256':sha(Path(comparison['performance_pdf'])),'native_reports':[{'effective_cfm':r['effective_cfm'],'pdf_sha256':r['pdf_sha256']} for r in independent['records']],'visual_review':{'critical_maximum_and_minimum_actual_native_pdf_pages_inspected':True,'all49_actual_pdf_pages_visually_inspected':False},'limits':['L/s inputs are represented by nearest whole CFM; effective flows retained for every row','Selected throw is reported in feet despite misleading Throw m label; table unit independently checked','Native throw output has finite display resolution; no unverified precision or uncertainty model added','Raw native pressure w.c. is not adopted as total or static pressure without reference confirmation','Native selected NC10 with table dash is retained as qualified null, not NC10 compliance','Original classroom170.1W/m2 versus160W/m2 load-band conflict remains','All49 native source PDFs and runtime records remain private; no design or ADPI acceptance follows'],'ADPI_verified':False,'design_accepted':False}
(O/'review.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k not in ['native_reports','minimum_case','maximum_case','limits']}))

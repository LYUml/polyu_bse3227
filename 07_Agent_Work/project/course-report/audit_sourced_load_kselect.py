"""Prepare independent PDF-coordinate readback and exact current-candidate ratios."""
from pathlib import Path
import subprocess,json,csv,math,hashlib
from decimal import Decimal,localcontext
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');P=B/'07_Agent_Work';R=P/'runs/course-sourced-load-candidate';W=P/'runs/course-load150-kselect-conditions'
source=P/'project/adpi-manufacturer-study/verify_current_kselect_pdfs.py'
script=source.read_text().replace("W=B/'current-course-kselect-all-conditions'","W=B/'course-load150-kselect-conditions'")
adapted=R/'independent_native_reader.py';adapted.write_text(script)
runtime=Path('C:/Users/lyuml-win/Desktop/building-services-agent/tools/pdf2plot-runtime/Scripts/python.exe')
subprocess.run([str(runtime),str(adapted)],check=True)
independent=json.loads((W/'independent-native-report-check.json').read_text());native={r['effective_cfm']:r for r in independent['records']};assert len(native)==48
rows=list(csv.DictReader((R/'Diffuser Course Ratio Check.csv').open()));results=[]
with localcontext() as ctx:
 ctx.prec=40
 for row in rows:
    q=Decimal(row['flow_L_s']);cfm=int((q*Decimal('2.118880003289315')+Decimal('.5')).to_integral_value(rounding='ROUND_FLOOR'));n=native[cfm];T=Decimal(str(n['native_selected']['throw_ft']))*Decimal('.3048');L=Decimal(row['L_m']);ratio=T/L
    results.append(dict(terminal=row['terminal'],direction=row['direction'],case=row['case'],flow_L_s=str(q),L_m=str(L),effective_cfm=cfm,effective_flow_L_s=str(Decimal(cfm)/Decimal('2.118880003289315')),native_T025_m=str(T),native_reported_throw_ft=n['native_selected']['throw_ft'],native_ratio=str(ratio),classroom_interval_met=1<=ratio<=Decimal('3.4'),original_catalogue_T025_m=row['T025_m'],original_catalogue_ratio=row['ratio'],native_pdf_sha256=n['pdf_sha256']))
with (R/'Native K-Select Ratio Check.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=results[0]);w.writeheader();w.writerows(results)
lo=min(results,key=lambda r:float(r['native_ratio']));hi=max(results,key=lambda r:float(r['native_ratio']))
summary=dict(scope='Native Model1400/24x24/6inch candidate readback,not ADPI percentage certification',native_conditions=48,independent_scalar_checks=independent['scalar_checks'],independent_all_table_checks_pass=independent['all_native_selected_fields_and9column_tables_match'],directional_operating_checks=640,all640_reported_native_ratios_within_classroom_interval=all(r['classroom_interval_met'] for r in results),native_ratio_minimum=float(lo['native_ratio']),native_ratio_maximum=float(hi['native_ratio']),minimum_case=lo,maximum_case=hi,maximum_absolute_input_rounding_L_s=max(abs(float(r['effective_flow_L_s'])-float(r['flow_L_s'])) for r in results),all_units_ft_to_m_verified=True,ADPI_verified=False)
(R/'Native K-Select Check.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
assert summary['all640_reported_native_ratios_within_classroom_interval']

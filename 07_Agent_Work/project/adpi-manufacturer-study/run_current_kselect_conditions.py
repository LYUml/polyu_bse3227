from pathlib import Path
import csv,json,math,subprocess,time,hashlib
P=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');B=P/'07_Agent_Work/runs';out=B/'current-course-kselect-all-conditions';out.mkdir(exist_ok=False)
exe=Path('C:/Users/lyuml-win/Desktop/k-select-agent-toolkit/.venv/Scripts/k-select.exe')
rows=list(csv.DictReader((P/'05_Calculations/Connection_Layout/Diffuser Course Ratio Check.csv').open()))
cfms=sorted({math.floor(float(r['flow_L_s'])*2.118880003289315+.5) for r in rows})
reused={331:B/'current-course-kselect-critical-maximum',107:B/'current-course-kselect-critical-minimum'}
records=[];started=time.time()
for cfm in cfms:
 if cfm in reused:
  folder=reused[cfm];mode='reuse exact verified integer-CFM report'
 else:
  folder=out/f'cfm-{cfm:04}'
  args=[str(exe),'--json','performance','--airflow',str(cfm),'--airflow-unit','cfm','--model','1400','--neck-in','8','--module','24x24','--output-directory',str(folder)]
  result=subprocess.run(args,capture_output=True,text=True,encoding='utf-8')
  (out/f'cfm-{cfm:04}-command.json').write_text(result.stdout,encoding='utf-8')
  if result.returncode!=0:
   (out/'failure.json').write_text(json.dumps({'cfm':cfm,'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr},indent=2),encoding='utf-8')
   raise RuntimeError('Native run failed; stop and inspect before any retry')
  mode='new native execution'
 result=json.loads((folder/'result.json').read_text(encoding='utf-8'))
 assert result['ok'] and all(result['checks'].values())
 assert result['report']['selected']['airflow_cfm']==cfm
 pdf=folder/'performance.pdf'
 assert hashlib.sha256(pdf.read_bytes()).hexdigest()==result['report']['sha256']
 records.append({'effective_cfm':cfm,'folder':str(folder),'mode':mode,'pdf_sha256':result['report']['sha256']})
 (out/'progress.json').write_text(json.dumps({'completed':len(records),'total':len(cfms),'elapsed_seconds':time.time()-started,'records':records},indent=2),encoding='utf-8')
 print(json.dumps({'completed':len(records),'total':len(cfms),'effective_cfm':cfm}),flush=True)
(out/'batch-complete.json').write_text(json.dumps({'native_conditions':len(records),'new_native_executions':len(records)-2,'reused_conditions':2,'elapsed_seconds':time.time()-started,'records':records},indent=2),encoding='utf-8')

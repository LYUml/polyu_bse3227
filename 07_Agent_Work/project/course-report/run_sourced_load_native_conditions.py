"""Reuse verified K-Select CLI and one exact pilot; stop on any native failure."""
import json,csv,math,time,subprocess,hashlib
from pathlib import Path
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');P=B/'07_Agent_Work';R=P/'runs/course-load150-kselect-conditions';R.mkdir(exist_ok=False)
cli=Path('C:/Users/lyuml-win/Desktop/k-select-agent-toolkit/.venv/Scripts/k-select.exe')
source=P/'runs/course-sourced-load-candidate/Diffuser Course Ratio Check.csv';rows=list(csv.DictReader(source.open()))
cfms=sorted({math.floor(float(r['flow_L_s'])*2.118880003289315+.5) for r in rows});started=time.time();records=[]
for cfm in cfms:
    reused=cfm==100
    folder=P/'runs/course-load150-critical-100' if reused else R/f'cfm-{cfm:04}'
    if not reused:
        result=subprocess.run([str(cli),'--json','performance','--airflow',str(cfm),'--airflow-unit','cfm','--model','1400','--neck-in','6','--module','24x24','--output-directory',str(folder)],capture_output=True,text=True,encoding='utf-8')
        (R/f'cfm-{cfm:04}-command.json').write_text(result.stdout)
        if result.returncode:
            (R/'failure.json').write_text(json.dumps(dict(cfm=cfm,returncode=result.returncode,stdout=result.stdout,stderr=result.stderr),indent=2));raise RuntimeError('Native failure: inspect before any retry')
    value=json.loads((folder/'result.json').read_text());assert value['ok'] and all(value['checks'].values())
    assert value['report']['neck_in']==6 and value['report']['module']=='24x24' and value['report']['selected']['airflow_cfm']==cfm
    assert hashlib.sha256((folder/'performance.pdf').read_bytes()).hexdigest()==value['report']['sha256']
    records.append(dict(effective_cfm=cfm,folder=str(folder),pilot_reused=reused,pdf_sha256=value['report']['sha256']))
    (R/'progress.json').write_text(json.dumps(dict(completed=len(records),total=len(cfms),elapsed_seconds=time.time()-started,records=records),indent=2))
    print(json.dumps(dict(completed=len(records),total=len(cfms),cfm=cfm)),flush=True)
(R/'batch-complete.json').write_text(json.dumps(dict(native_conditions=len(records),pilot_conditions_reused=1,new_in_batch=len(records)-1,source_csv_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),records=records,elapsed_seconds=time.time()-started),indent=2))

from pathlib import Path
import fitz,json,hashlib
P=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');S=P/'07_Agent_Work/project/adpi-manufacturer-study/plaque-source';B=P/'07_Agent_Work/runs/manufacturer-plqr-source';f=S/'PLQ 5PLQ PLQR MiniCatalog.pdf';d=fitz.open(f);w=d[14].get_text('words');tables=json.loads((B/'source-tables.json').read_text());rows=[r for table in tables.values() for r in table];anchors=sorted([x for x in w if 80<(x[0]+x[2])/2<110 and x[4].isdigit() and 100<=int(x[4])<=1100 and x[1]>100],key=lambda x:x[1]);assert len(anchors)==54
checks=0
for anchor,row in zip(anchors,rows):
 line=[x for x in w if abs(x[1]-anchor[1])<.1]
 def col(lo,hi):
  v=[x[4] for x in sorted(line,key=lambda x:x[0]) if lo<(x[0]+x[2])/2<hi];assert v;return v
 for key,lo,hi in [('flow_L_s',310,335),('static_pressure_Pa',337,369),('total_pressure_Pa',370,401)]:
  v=col(lo,hi);assert len(v)==1 and float(v[0])==row[key];checks+=1
 v=[float(x) for x in col(402,457) if x!='-'];assert len(v)==3
 for key,value in zip(('T075_m','T050_m','T025_m'),v):assert row[key]==value;checks+=1
 nc=col(255,278);assert len(nc)==1;assert (None if nc[0]=='-' else float(nc[0]))==row['NC'];checks+=1
r={'source_pdf_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'source_tables_sha256':hashlib.sha256((B/'source-tables.json').read_bytes()).hexdigest(),'independent_engine':'PyMuPDF1.26.7 native word coordinates/baselines versus pypdf7.0.0 token parser','metric_rows':54,'metric_throw_triplets':54,'scalar_checks':checks,'actual_source_pages_rendered_and_viewed':[2,14,15],'all_match':True,'ADPI_verified':False};(B/'independent-source-check.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))

import fitz,json,re,hashlib
from pathlib import Path
P=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');B=P/'07_Agent_Work/runs/manufacturer-modular-core-source';S=P/'07_Agent_Work/project/adpi-manufacturer-study/modular-core-source'
d=fitz.open(S/'124051240_PerformanceData.pdf');r=json.loads((B/'source-rows.json').read_text())['rows'];checks=0
def number(s):return float(s)
def triplet(s):return [float(x) for x in re.sub(r'\s','',s).split('-')]
for pi,page in enumerate(d):
 w=page.get_text('words')
 anchors=sorted([t for t in w if 75<t[0]<90 and t[4].isdigit() and 100<=int(t[4])<=1100 and 150<t[1]<720],key=lambda t:t[1])
 assert len(anchors)==45,(pi,len(anchors))
 for j,anchor in enumerate(anchors):
  row=r[(pi%2)*45+j];y=anchor[1];line=[t for t in w if abs(t[1]-y)<.1]
  def col(lo,hi):
   values=[t[4] for t in line if lo<(t[0]+t[2])/2<hi];assert len(values)==1,(pi,j,lo,values)
   return values[0]
  if pi<2:
   assert number(col(300,325))==row['flow_L_s'];checks+=1
   assert number(col(325,355))==row['one_core_static_Pa'];checks+=1
   assert number(col(355,390))==row['one_core_total_Pa'];checks+=1
   assert triplet(col(390,440))==row['core_throw_T075_T050_T025_m']['1'];checks+=3
   nc=col(245,268);assert (None if nc=='-' else number(nc))==row['one_core_NC'];checks+=1
  else:
   assert number(col(330,350))==row['flow_L_s'];checks+=1
   for core,lo,hi in [(2,360,415),(3,425,480),(4,490,545)]:
    assert triplet(col(lo,hi))==row['core_throw_T075_T050_T025_m'][str(core)];checks+=3
report={'independent_engine':'PyMuPDF1.26.7 native word bounding boxes and row baselines; independent of pypdf token order parser','all90_flow_rows_and360_metric_throw_triplets_match':True,'scalar_checks':checks,'original_pdf_sha256':hashlib.sha256((S/'124051240_PerformanceData.pdf').read_bytes()).hexdigest(),'extracted_rows_sha256':hashlib.sha256((B/'source-rows.json').read_bytes()).hexdigest(),'scope':'Source transcription only, not physical product/ADPI acceptance'}
(B/'independent-source-check.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))

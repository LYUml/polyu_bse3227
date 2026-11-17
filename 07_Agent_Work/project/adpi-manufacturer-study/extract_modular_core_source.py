from pathlib import Path
from pypdf import PdfReader
import json,hashlib
P=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');S=P/'07_Agent_Work/project/adpi-manufacturer-study/modular-core-source';B=P/'07_Agent_Work/runs';O=B/'manufacturer-modular-core-source';O.mkdir(exist_ok=False)
pdf=S/'124051240_PerformanceData.pdf';d=PdfReader(pdf);one=[];multi=[]
for i,p in enumerate(d.pages):
 count=25 if i<2 else 34
 rows=[l.split() for l in p.extract_text().splitlines() if len(l.split())==count and l.split()[0].isdigit()]
 assert len(rows)==45
 (one if i<2 else multi).extend(rows)
result=[]
for j,(a,b) in enumerate(zip(one,multi)):
 neck=6+2*(j//9);assert float(a[11])==float(b[18])
 assert all(a[k]=='-' for k in [5,7,15,17])
 assert all(b[k]=='-' for k in [3,5,8,10,13,15,20,22,25,27,30,32])
 cores={'1':[float(a[k]) for k in [14,16,18]]}
 for core,offset in [(2,19),(3,24),(4,29)]:cores[str(core)]=[float(b[offset+x]) for x in [0,2,4]]
 result.append({'neck_square_inch':neck,'flow_L_s':float(a[11]),'neck_velocity_m_s':float(a[10]),'one_core_static_Pa':float(a[12]),'one_core_total_Pa':float(a[13]),'one_core_NC':None if a[9]=='-' else float(a[9]),'core_throw_T075_T050_T025_m':cores})
assert len(result)==90
assert [result[i*9]['flow_L_s'] for i in range(10)]==[35,63,98,142,193,252,319,262,159,189]
(O/'source-rows.json').write_text(json.dumps({'source_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'rows':result,'scope':'Native published metric no-damper data. Ps/Pt/NC available only for1-core table; never transferred to other pattern counts.'},indent=2),encoding='utf-8')
comp=json.loads((B/'manufacturer-adpi-comparison/comparison.json').read_text());f=list(Path(comp['workflow']).glob('*/allocation.json'));assert len(f)==1
allocation=json.loads(f[0].read_text());terminals=[]
for t in allocation['terminals']:
 options=[]
 for n in range(6,25,2):
  rs=[r for r in result if r['neck_square_inch']==n]
  if rs[0]['flow_L_s']<=t['minimum_flow_L_s']<=t['maximum_flow_L_s']<=rs[-1]['flow_L_s']:options.append(n)
 terminals.append({'terminal':t['id'],'maximum_flow_L_s':t['maximum_flow_L_s'],'minimum_flow_L_s':t['minimum_flow_L_s'],'simultaneous_catalogue_flow_necks_square_inch':options})
review={'source_downloads':json.loads((S/'source-download.json').read_text()),'rows':90,'source_throw_triplets':360,'terminal_count':80,'terminals_with_no_both_flow_neck':sum(not t['simultaneous_catalogue_flow_necks_square_inch'] for t in terminals),'terminals':terminals,'pattern_mapping':{'1_core_throw':'four-way, one core per direction','2_core_throw':'stronger jet in some three-way arrangements, or each jet in opposite two-way arrangement','3_core_throw':'stronger jet in shown adjacent two-way arrangement','4_core_throw':'one-way arrangement'},'manufacturer_ADPI_chart_load_Btuh_ft2':20,'current_maximum_conditional_load_Btuh_ft2':170.1/(1055.05585262/3600/.3048**2),'source_pages_rendered_viewed':{'dimension':[2],'performance':[1,2,3,4],'minicatalog':[5]},'limits':['No Model1400 ADPI curves transferred to1240','Published4way ADPI spacing charts are20Btuh/ft2, not current~53.92','Unsupported minimum operating flow is missing data, not proven equipment failure','No product/pattern adopted or native candidate issued'],'design_accepted':False}
(O/'review.json').write_text(json.dumps(review,indent=2),encoding='utf-8')
print('source rows',len(result),'no-neck',review['terminals_with_no_both_flow_neck'])

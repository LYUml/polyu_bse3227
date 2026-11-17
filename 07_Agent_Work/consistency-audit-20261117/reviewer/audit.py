from pathlib import Path
import csv,json,re,math,hashlib
from pypdf import PdfReader
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227')
O=B/'07_Agent_Work/consistency-audit-20261117/reviewer'
I=B/'07_Agent_Work/runs/course-refined-report-inputs'
load=lambda p:json.loads(p.read_text(encoding='utf8'))
rows=lambda p:list(csv.DictReader(p.open(encoding='utf-8-sig')))
pdf=PdfReader(B/'00_Submit/BSE3227_HVAC_Design_Report.pdf'); pages=[p.extract_text() for p in pdf.pages]
allocation=load(I/'allocation.json'); terms={t['id']:t for t in allocation['terminals']}
ratios=rows(B/'00_Submit/Calculations/Diffuser Course Ratio Check.csv'); native=rows(I/'Native K-Select Ratio Check.csv')
groups=rows(B/'00_Submit/Calculations/VAV Connection Schedule.csv'); ducts=rows(B/'00_Submit/Calculations/Duct Sizing.csv')
online={r['Section']:r for r in rows(B/'05_Calculations/Connection_Layout/Online Ductulator Check.csv')}
checks=[]; failures=[]
def ck(name,ok,detail=None):
 checks.append({'check':name,'pass':bool(ok),'detail':detail})
 if not ok: failures.append(checks[-1])
def table(ps,pattern):
 text='\n'.join(pages[i-1] for i in ps)
 return re.findall(pattern,text)
num=r'([\d.]+)'
A=table([9,10],r'(SD-\d{2})\s+'+'\s+'.join([num]*6))
ck('Appendix A complete 80 unique rows',len(A)==80 and len({r[0] for r in A})==80)
for r in A:
 tid=r[0]; rr=[v for v in ratios if v['terminal']==tid]; mx=[v for v in rr if v['case']=='maximum']; mn=[v for v in rr if v['case']=='minimum']
 expected=[f"{terms[tid]['maximum_flow_L_s']:.2f}",f"{terms[tid]['minimum_flow_L_s']:.2f}",f"{float(mx[0]['T025_m']):.3f}",f"{float(mn[0]['T025_m']):.3f}",f"{max(float(v['ratio']) for v in mx):.4f}",f"{min(float(v['ratio']) for v in mn):.4f}"]
 ck('A '+tid,list(r[1:])==expected,{'pdf':r[1:],'expected':expected} if list(r[1:])!=expected else None)
BB=table([11,12],r'(SD-\d{2})\s+'+'\s+'.join([num]*4))
ck('Appendix B complete 80 rows',len(BB)==80 and len({r[0] for r in BB})==80)
for r in BB:
 expected=[f"{float(next(v['L_m'] for v in ratios if v['terminal']==r[0] and v['direction']==direction)):.4f}" for direction in ['west','east','south','north']]
 ck('B '+r[0],list(r[1:])==expected)
C=table([13],r'(VAV-\d{2})\s+(SD-\d{2}, SD-\d{2}, SD-\d{2}, SD-\d{2})\s+'+num+r'\s+'+num+r'\s+'+num+'-'+num)
ck('Appendix C complete 20 rows',len(C)==20)
centres=load(I/'vav-centres.json'); distances=[]; membership=[]
for r in C:
 g=next(g for g in groups if g['VAV']==r[0]); expected=[g['Diffuser outlets'],g['Qmax L/s'],g['Qmin L/s'],g['Min plan m'],g['Max plan m']]
 ck('C '+r[0],list(r[1:])==expected)
 members=g['Diffuser outlets'].split(', '); membership+=members
 q=sum(terms[t]['maximum_flow_L_s'] for t in members); qm=sum(terms[t]['minimum_flow_L_s'] for t in members)
 ds=[math.dist(centres[r[0]],terms[t]['center_m']) for t in members]; distances+=ds
 ck('group sums and lengths '+r[0],[f'{q:.1f}',f'{qm:.1f}',f'{min(ds):.3f}',f'{max(ds):.3f}']==list(r[2:]))
ck('Every diffuser appears once in grouping',sorted(membership)==sorted(terms))
D=table([14,15],r'([AD]-\d{2})\s+'+num+r'\s+(\d+) x (\d+)\s+'+'\s+'.join([num]*4))
ck('Appendix D complete 47 unique rows',len(D)==47 and len({r[0] for r in D})==47)
for r in D:
 d=next(d for d in ducts if d['Section']==r[0]); expected=[f"{float(d['Flow L/s']):.2f}",f"{float(d['Width mm']):.0f}",f"{float(d['Height mm']):.0f}",f"{float(d['Velocity m/s']):.3f}",online[r[0]]['Online friction display Pa/m'],f"{float(d['Friction Pa/m']):.4f}",f"{float(d['Aspect ratio']):.2f}"]
 ck('D '+r[0],list(r[1:])==expected,{'pdf':r[1:],'expected':expected} if list(r[1:])!=expected else None)
 v=float(d['Flow L/s'])*1000/(float(d['Width mm'])*float(d['Height mm']))
 ck('duct velocity '+r[0],abs(v-float(d['Velocity m/s']))<1e-10)
for r in ratios:
 ck('ratio arithmetic '+r['terminal']+' '+r['direction']+' '+r['case'],abs(float(r['T025_m'])/float(r['L_m'])-float(r['ratio']))<1e-12)
ck('640 unique ratio cases',len(ratios)==640 and len({(r['terminal'],r['direction'],r['case']) for r in ratios})==640)
ck('all 80 turndown ratios exact 40%',all(abs(t['minimum_flow_L_s']/t['maximum_flow_L_s']-.4)<1e-14 for t in terms.values()))
q=sum(t['maximum_flow_L_s'] for t in terms.values()); qm=sum(t['minimum_flow_L_s'] for t in terms.values()); qcalc=1022*189*.9/(1.2*1006*12)*1000
ck('airflow independently recomputed',abs(q-qcalc)<1e-8)
stats={'report_pages':len(pdf.pages),'A_numeric_fields':len(A)*6,'B_numeric_fields':len(BB)*4,'C_rows':len(C),'D_numeric_fields':len(D)*7,'total_flow_L_s':q,'minimum_flow_L_s':qm,'maximum_plan_flex_m':max(distances),'conditional_max_flex_m':max(distances)+.5,'original_ratio_range':[min(float(r['ratio']) for r in ratios),max(float(r['ratio']) for r in ratios)],'native_ratio_range':[min(float(r['native_ratio']) for r in native),max(float(r['native_ratio']) for r in native)],'boundary_direction_count':sum(r['case']=='maximum' and r['L_reference']!='opposing_diffuser_midplane' for r in ratios),'native_unique_cfm':len({r['effective_cfm'] for r in native}),'max_native_flow_rounding_L_s':max(abs(float(r['effective_flow_L_s'])-float(r['flow_L_s'])) for r in native)}
for file in ['Diffuser Course Ratio Check.csv','VAV Connection Schedule.csv']:
 ck('input matches submit '+file,(I/file).read_bytes()==(B/'00_Submit/Calculations'/file).read_bytes())
result={'stats':stats,'check_count':len(checks),'failures':failures,'checks':checks}
(O/'results.json').write_text(json.dumps(result,indent=2),encoding='utf8'); print(json.dumps({'stats':stats,'checks':len(checks),'failures':failures},indent=2))

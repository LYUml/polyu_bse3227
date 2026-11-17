from pathlib import Path
import json,csv,hashlib,math,re
import ezdxf
from pypdf import PdfReader
B=Path(__file__).resolve().parents[2]
A=B.parent/'building-services-agent'
O=Path(__file__).parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
rows=lambda p:list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result={}
package=read(B/'05_Calculations/Submission_Package_Check.json')
result['package_copies']=[dict(file=r['file'],source=r['source'],copies_match=sha(B/r['file'])==sha(B/r['source']),recorded_hash_matches=sha(B/r['file'])==r['sha256']) for r in package['files']]
I=B/'07_Agent_Work/runs/course-refined-report-inputs'
alloc=read(I/'allocation.json'); terms={t['id']:t for t in alloc['terminals']}
ducts=rows(B/'00_Submit/Calculations/Duct Sizing.csv'); groups=rows(B/'00_Submit/Calculations/VAV Connection Schedule.csv'); ratios=rows(B/'00_Submit/Calculations/Diffuser Course Ratio Check.csv')
result['row_counts']={'ducts':len(ducts),'groups':len(groups),'ratios':len(ratios),'terminals':len(terms)}
result['load_recomputed']={'total_kW':1022*189/1000,'sensible_kW':1022*189*.9/1000,'flow_L_s':1022*189*.9/(1.2*1006*12)*1000,'terminal_sum_L_s':sum(t['maximum_flow_L_s'] for t in terms.values()),'all_minimum_40pct':all(math.isclose(t['minimum_flow_L_s'],t['maximum_flow_L_s']*.4,abs_tol=1e-10) for t in terms.values())}
errors=[]
centres=read(I/'vav-centres.json'); lengths=[]; membership=[]
for g in groups:
    ids=g['Diffuser outlets'].split(', '); membership+=ids
    q=sum(terms[t]['maximum_flow_L_s'] for t in ids)
    ds=[math.dist(terms[t]['center_m'],centres[g['VAV']]) for t in ids]; lengths+=ds
    expected=[f'{q:.1f}',f'{q*.4:.1f}',f'{min(ds):.3f}',f'{max(ds):.3f}',str(len(ids))]
    actual=[g[k] for k in ['Qmax L/s','Qmin L/s','Min plan m','Max plan m','Outlets']]
    if expected!=actual:errors.append({'group':g['VAV'],'expected':expected,'actual':actual})
for r in ducts:
    q,w,h=[float(r[k]) for k in ['Flow L/s','Width mm','Height mm']]
    if not math.isclose(q*1000/w/h,float(r['Velocity m/s']),abs_tol=1e-10):errors.append({'velocity':r['Section']})
    if not math.isclose(max(w,h)/min(w,h),float(r['Aspect ratio']),abs_tol=1e-10):errors.append({'aspect':r['Section']})
for r in ratios:
    if not math.isclose(float(r['T025_m'])/float(r['L_m']),float(r['ratio']),abs_tol=1e-10):errors.append({'ratio':r['terminal']})
    key='maximum_flow_L_s' if r['case']=='maximum' else 'minimum_flow_L_s'
    if not math.isclose(float(r['flow_L_s']),terms[r['terminal']][key],abs_tol=1e-10):errors.append({'ratio_flow':r['terminal']})
result['recomputation']={'errors':errors,'unique_members':len(set(membership)),'memberships':len(membership),'ratio_min':min(float(r['ratio']) for r in ratios),'ratio_max':max(float(r['ratio']) for r in ratios),'maximum_plan_flex_m':max(lengths),'total_plan_flex_m':sum(lengths),'conditional_max_plus_assumed_0_5_m':max(lengths)+.5}
native=ezdxf.readfile(B/'07_Agent_Work/runs/course-diffuser-native-final/reopened/source-export.dxf').modelspace()
texts=[e for e in native.query('TEXT') if e.dxf.layer=='BSA_SCHEDULE']; native_errors=[]
for r in ducts:
    found=[e for e in texts if e.dxf.text==r['Section']]
    if len(found)!=1:native_errors.append({'id':r['Section'],'found':len(found)});continue
    cells=sorted([e for e in texts if abs(e.dxf.insert.y-found[0].dxf.insert.y)<1e-8],key=lambda e:e.dxf.insert.x)
    expected=[r['Section'],f"{float(r['Flow L/s']):.1f}",f"{float(r['Width mm']):.0f} x {float(r['Height mm']):.0f}",f"{float(r['Velocity m/s']):.2f}",f"{float(r['Friction Pa/m']):.3f}"]
    if [e.dxf.text for e in cells]!=expected:native_errors.append({'id':r['Section'],'expected':expected,'actual':[e.dxf.text for e in cells]})
panels=[e for e in native if e.dxf.layer=='BSA_DIFFUSER' and e.dxftype()=='LWPOLYLINE']
for tid,t in terms.items():
    matches=[p for p in panels if math.dist([sum(v[0] for v in p.get_points())/len(p)/1000,sum(v[1] for v in p.get_points())/len(p)/1000],t['center_m'])<1e-8]
    if len(matches)!=1:native_errors.append({'panel':tid,'matches':len(matches)})
flex=[e for e in native.query('LINE') if e.dxf.layer=='BSA_FLEX']
for g in groups:
    for tid in g['Diffuser outlets'].split(', '):
        xy=terms[tid]['center_m']; c=centres[g['VAV']]
        def near(v,p):return math.dist([v.x/1000,v.y/1000],p)<1e-8
        matches=[e for e in flex if (near(e.dxf.start,xy) and near(e.dxf.end,c)) or (near(e.dxf.end,xy) and near(e.dxf.start,c))]
        if len(matches)!=1:native_errors.append({'flex':tid,'matches':len(matches)})
result['native_readback']={'errors':native_errors,'duct_rows':47,'duct_fields':235,'panels':len(panels),'flex':len(flex),'dwg_matches_saved_reopen_copy':sha(B/'00_Submit/Drawings/Supply Air Distribution.dwg')==sha(B/'07_Agent_Work/runs/course-diffuser-native-final/reopened/source-copy.dwg'),'fresh_autocad_open_performed':False}
vavdoc=ezdxf.readfile(B/'07_Agent_Work/runs/course-refined-vav-table/native/reopened/source-export.dxf')
vt=[e for e in vavdoc.modelspace().query('TEXT') if e.dxf.layer=='BSA_VAV_TABLE']; ve=[]
for g in groups:
    tags=[e for e in vt if e.dxf.text==g['VAV']]
    if len(tags)!=1:ve.append({'id':g['VAV'],'tags':len(tags)});continue
    cells=sorted([e for e in vt if abs(e.dxf.insert.y-tags[0].dxf.insert.y)<1e-8],key=lambda e:e.dxf.insert.x)
    if [e.dxf.text for e in cells]!=[g[k] for k in ['VAV','Diffuser outlets','Qmax L/s','Qmin L/s','Min plan m','Max plan m','Outlets']]:ve.append({'id':g['VAV']})
result['vav_native_table']={'rows':20,'fields':140,'errors':ve,'dwg_matches_reopened_copy':sha(B/'00_Submit/Drawings/VAV Connection Schedule.dwg')==sha(B/'07_Agent_Work/runs/course-refined-vav-table/native/reopened/source-copy.dwg')}
nr=rows(I/'Native K-Select Ratio Check.csv'); ne=[]
for r in nr:
    if not math.isclose(float(r['native_reported_throw_ft'])*.3048/float(r['L_m']),float(r['native_ratio']),abs_tol=1e-10):ne.append({'terminal':r['terminal'],'direction':r['direction'],'case':r['case']})
result['native_ratios']={'rows':len(nr),'errors':ne,'min':min(float(r['native_ratio']) for r in nr),'max':max(float(r['native_ratio']) for r in nr)}
from PIL import Image,ImageChops
result['report_embedded_drawing']={'comparison':'report page16 versus submitted drawing, Poppler1600px','pixel_identical':ImageChops.difference(Image.open(O/'report-plan.png'),Image.open(O/'drawing.png')).getbbox() is None}
comparisons={}
for name in ['bse3227-current-agent-package','bse3227-aligned-layout-package']:
    root=A/'runs'/name
    other=read(root/'workflow/air-allocation/allocation.json'); ot={t['id']:t for t in other['terminals']}
    ds=rows(root/'workflow/duct-schedule/schedule.csv'); od={r['Section']:r for r in ds}
    changes=[]
    for r in ducts:
        diff={k:{'agent':od[r['Section']][k],'project':r[k]} for k in r if k!='Section' and r[k]!=od[r['Section']][k]}
        if diff:changes.append({'id':r['Section'],'fields':diff})
    positions=[{'id':k,'agent':ot[k]['center_m'],'project':v['center_m'],'distance_m':math.dist(ot[k]['center_m'],v['center_m'])} for k,v in terms.items() if math.dist(ot[k]['center_m'],v['center_m'])>1e-8]
    flowdiff=[k for k,v in terms.items() if not math.isclose(v['maximum_flow_L_s'],ot[k]['maximum_flow_L_s'],abs_tol=1e-10)]
    ag=read(root/'terminal-review.json')['groups']; groupdiff=[]
    for g in groups:
        o=next(x for x in ag if x['id']==g['VAV']); ids=g['Diffuser outlets'].split(', ')
        oldids=[x['terminal'] for x in o['routes']]
        if set(ids)!=set(oldids):groupdiff.append({'id':g['VAV'],'members_changed':True})
        old=[x['plan_length_m'] for x in o['routes']]
        if f'{min(old):.3f}'!=g['Min plan m'] or f'{max(old):.3f}'!=g['Max plan m']:groupdiff.append({'id':g['VAV'],'agent_range':[min(old),max(old)],'project_range':[g['Min plan m'],g['Max plan m']]})
    nd=ezdxf.readfile(root/'workflow/native-sheet/reopened/source-export.dxf').modelspace()
    nt=[e for e in nd.query('TEXT') if e.dxf.layer=='BSA_SCHEDULE']; nerr=[]
    for r in ds:
        tags=[e for e in nt if e.dxf.text==r['Section']]
        if len(tags)!=1:nerr.append({'section':r['Section'],'tags':len(tags)});continue
        cells=sorted([e for e in nt if abs(e.dxf.insert.y-tags[0].dxf.insert.y)<1e-8],key=lambda e:e.dxf.insert.x)
        expected=[r['Section'],f"{float(r['Flow L/s']):.1f}",f"{float(r['Width mm']):.0f} x {float(r['Height mm']):.0f}",f"{float(r['Velocity m/s']):.2f}",f"{float(r['Friction Pa/m']):.3f}"]
        if [e.dxf.text for e in cells]!=expected:nerr.append({'section':r['Section'],'actual':[e.dxf.text for e in cells],'expected':expected})
    comparisons[name]={'position_differences':positions,'flow_differences':flowdiff,'duct_row_differences':changes,'vav_differences':groupdiff,'agent_pdf_pages':len(PdfReader(root/'report-pdf/HVAC System Design.pdf').pages),'agent_saved_native_duct_table_errors':nerr}
result['cross_repository']=comparisons
with (O/'cross-repository-differences.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['Category','ID','Field','Agent saved package','Current project'])
    c=comparisons['bse3227-current-agent-package']
    for r in c['position_differences']:w.writerow(['Diffuser position',r['id'],'XY m',r['agent'],r['project']])
    for r in c['duct_row_differences']:
        for k,v in r['fields'].items():w.writerow(['Duct schedule',r['id'],k,v['agent'],v['project']])
    for r in c['vav_differences']:w.writerow(['VAV connection',r['id'],'Length range m',r.get('agent_range'),r.get('project_range')])
for name,path in [('submission',B/'00_Submit/BSE3227_HVAC_Design_Report.pdf'),('agent',A/'runs/bse3227-current-agent-package/report-pdf/HVAC System Design.pdf')]:
    pdf=PdfReader(path)
    (O/(name+'-text.txt')).write_text('\n'.join(f'\n--- PAGE {i+1} ---\n'+(p.extract_text() or '') for i,p in enumerate(pdf.pages)),encoding='utf-8')
result['main_report_pages']=len(PdfReader(B/'00_Submit/BSE3227_HVAC_Design_Report.pdf').pages)
(O/'audit-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))

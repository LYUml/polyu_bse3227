import hashlib
import json
import re
import io
import tokenize
from pathlib import Path

B = Path('C:/Users/lyuml-win/Desktop/polyu_bse3227')
P = B/'07_Agent_Work/project/course-report'
source = Path('C:/Users/lyuml-win/Desktop/polyu_bse3125/04_Report/Private/group-details.json')
group = json.loads(source.read_text(encoding='utf-8'))
private = P/'Private'
private.mkdir(exist_ok=True)
(private/'group-details.json').write_text(json.dumps(dict(
    members=group['members'],
    basis='User confirmed same members as lighting; HVAC group number not inferred',
    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest()), indent=2), encoding='utf-8')

s = (P/'build_bse3125_style_report.py').read_text(encoding='utf-8')
s = s.replace("R=B/'07_Agent_Work/runs/course-report-bse3125-style'",
              "import os\nPUBLIC=os.environ.get('BSE3227_REPORT_PUBLIC')=='1'\nR=B/('07_Agent_Work/runs/course-report-citations-public' if PUBLIC else '07_Agent_Work/runs/course-report-citations-private')")
start = s.index("page('References')")
end = s.index('for start in range(0,80,40):', start)
s = s[:start] + '''page('References')
refs=json.loads((B/'07_Agent_Work/project/course-report/references-ieee.json').read_text(encoding='utf-8'))
for ref in refs:
 text=f"[{ref['id']}] "+ref['html']+f" Accessed: Nov. 17, 2026. [Online]. Available: <link href=\\"{ref['url']}\\">{ref['url']}</link>."
 p(text,ParagraphStyle('Ref',parent=body,fontSize=11,leading=14,spaceAfter=10,alignment=0,leftIndent=24,firstLineIndent=-24,splitLongWords=True))
''' + s[end:]
# Remap only the previous literal citation IDs; generated bibliography uses f strings.
citations = {'1':'', '2':'', '3':'[2]', '4':'[3]', '5':'[5]', '6':'[1]', '7':'[6]'}
s = tokenize.untokenize([
    token._replace(string=re.sub(r'\[([1-7])\]', lambda m: citations[m[1]], token.string))
    if token.type == tokenize.STRING else token
    for token in tokenize.generate_tokens(io.StringIO(s).readline)
])
s = s.replace('required by the assignment .', 'required by the assignment.')
s = s.replace('classroom guide .', 'adopted design basis.')
s = s.replace('following the classroom method .', 'as an explicit assumption of the planar design.')
s = s.replace('4:1 .', '4:1.')
s = s.replace('manufacturer Type 3 curve.', 'manufacturer Type 3 curve [4].')
s = s.replace('The written classroom guide gives an office cooling allowance of 189 W/m<super>2</super> and an approximate sensible heat factor of 0.90 adopted design basis.',
              'The adopted preliminary design uses an office cooling allowance of 189 W/m<super>2</super> and an approximate sensible heat factor of 0.90.')
s = s.replace('The written classroom guide gives an office cooling allowance of 189 W/m<super>2</super> and an approximate sensible heat factor of 0.90 .',
              'The adopted preliminary design uses an office cooling allowance of 189 W/m<super>2</super> and an approximate sensible heat factor of 0.90.')
s = s.replace('Course: section sizing [2,5]', 'Course: section sizing [5]')
s = s.replace('spaceAfter=15))', '''spaceAfter=8))
if not PUBLIC:
 group=json.loads((B/'07_Agent_Work/project/course-report/Private/group-details.json').read_text(encoding='utf-8'))
 members=sorted(group['members'],key=lambda m:m['name'].casefold())
 for row in [members[:3],members[3:]]:
  labels=[html.escape(m['name']+' '+m['student_id']) for m in row]
  p(('&#160;'*7).join(labels),ParagraphStyle('Members',parent=small,fontSize=10,leading=12,alignment=TA_CENTER,spaceAfter=2))
 story.append(Spacer(1,9))''')
s = s.replace("paths['course_basis']=", "paths['references_ieee']=B/'07_Agent_Work/project/course-report/references-ieee.json'\nif not PUBLIC:paths['group_members']=B/'07_Agent_Work/project/course-report/Private/group-details.json'\npaths['course_basis']=")
(P/'build_course_report_members_references.py').write_text(s, encoding='utf-8')

refs = [
    dict(id=1, html='Fire Services Department, <i>Fire Safety Requirements for Mechanical Ventilating Systems</i>, FSD Circular Letter no. 2/2023. Hong Kong: Government of the Hong Kong Special Administrative Region, Jun. 7, 2023, paras. 7.2-7.4.', url='https://www.hkfsd.gov.hk/eng/source/licensing/MECHANICAL_VS_EN_2_2023.pdf'),
    dict(id=2, html='Krueger, "1400, 51400, M1400, M51400 published performance data," 2012, p. B1-12.', url='https://www.krueger-hvac.com/file/3118/1400_51400_M1400_M51400_PublishedPerformanceData.pdf'),
    dict(id=3, html='Krueger, "K-Select selection software."', url='https://www.krueger-hvac.com/public/software/k-select'),
    dict(id=4, html='Krueger, "Air distribution engineering," 2012, pp. a1-9-a1-11.', url='https://www.krueger-hvac.com/file/9261/GRD_Engineering.pdf'),
    dict(id=5, html='Ductulator.com, "Ductulator (Metric)."', url='https://ductulator.com/metric/'),
    dict(id=6, html='Electrical and Mechanical Services Department, <i>Code of Practice for Energy Efficiency of Building Services Installation</i>, 2024 ed. Hong Kong: Government of the Hong Kong Special Administrative Region, 2024, sec. 6.', url='https://www.emsd.gov.hk/beeo/en/pee/BEC_2024_ENG.pdf'),
]
(P/'references-ieee.json').write_text(json.dumps(refs, indent=2), encoding='utf-8')
print('Prepared local report inputs and bibliography; no identities printed.')

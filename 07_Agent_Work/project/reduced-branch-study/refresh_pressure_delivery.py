"""Refresh only calculation delivery, preserving native drawing evidence."""
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
RUN=ROOT/'07_Agent_Work/runs/reduced-branch-network-reviewed'
SOURCE=RUN/'one-plane-source-extension-reviewed'
OUT=SOURCE/'delivery-reviewed'
OUT.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
review=json.loads((SOURCE/'review.json').read_text())
assert all(sha(Path(p))==h for p,h in review['inputs'].items())
report=ROOT/'05_Calculations/Supply Network Pressure Review.html'
old=report.read_text(encoding='utf-8')
(OUT/'previous-pressure-review.html').write_text(old,encoding='utf-8')
tables=[];expected=[]
for name,folder in [('maximum',RUN),('minimum',RUN/'minimum-flow')]:
    case=json.loads((folder/'analysis.json').read_text())
    ledger=json.loads((SOURCE/name/'pressure-ledger.json').read_text())
    assert ledger['numerically_unresolved_fitting_path_count']==33
    cells=[]
    for row in ledger['outlet_paths']:
        port=case['port_flows'][row['outlet_port_guid']]
        values=[port['source_section'],f"{port['flow_m3_s']*1000:.3f}",f"{row['known_straight_friction_Pa']:.4f}",f"{row['conditional_signed_table_subtotal_Pa']:.4f}",str(len(row['numerically_unresolved_fitting_paths'])),'Unknown']
        expected.extend(values)
        cells.append('<tr>'+''.join('<td>'+html.escape(v)+'</td>' for v in values)+'</tr>')
    tables.append(''.join(cells))
new=old.replace('63 fitting paths:29 with conditional source values and 34 without','63 fitting paths:30 with conditional source values and 33 without')
assert new!=old
cursor=0
for table in tables:
    start=new.index('</th></tr>',cursor)+len('</th></tr>')
    end=new.index('</table>',start)
    new=new[:start]+table+new[end:]
    cursor=start+len(table)+len('</table>')
note='<p>One additional existing one-plane contraction now uses the tentative printed19 Fitting4-2 inlet-reference data. Both literal repeated30-degree columns agree at the selected contraction rows; the common ordinate and unambiguous45-degree ordinate are used without correcting a header or snapping the native angle. Independent Decimal checks agree at maximum and minimum flow; all other fitting results and all geometry are unchanged. This adds calculation evidence, not a pressure-saving claim. Physical applicability remains unverified.</p>'
new=new.replace('<h2>Source and scope</h2>',note+'<h2>Source and scope</h2>')
class Cells(HTMLParser):
    def __init__(self):super().__init__();self.active=False;self.values=[]
    def handle_starttag(self,tag,attrs):
        if tag=='td':self.active=True;self.values.append('')
    def handle_data(self,data):
        if self.active:self.values[-1]+=data
    def handle_endtag(self,tag):
        if tag=='td':self.active=False
parser=Cells();parser.feed(new)
assert parser.values==expected and len(expected)==240
report.write_text(new,encoding='utf-8')
scope=ROOT/'03_Design_Drawings/Network_Study/Review scope.md'
text=scope.read_text(encoding='utf-8');assert 'retain 34 unknown' in text
scope.write_text(text.replace('retain 34 unknown','retain 33 unknown'),encoding='utf-8')
check=ROOT/'05_Calculations/Supply_Network_Study_Check.json'
summary=json.loads(check.read_text())
for prefix in ['maximum','minimum']:
    assert summary[prefix+'_conditional_values']==29 and summary[prefix+'_numeric_gaps']==34
    summary[prefix+'_conditional_values']=30;summary[prefix+'_numeric_gaps']=33
summary.update(new_supported_one_plane_transition_values=1,one_plane_independent_decimal_verified=True,
    one_plane_review_sha256=sha(SOURCE/'review.json'),pressure_report_sha256=sha(report))
check.write_text(json.dumps(summary,indent=2))
agent=Path('C:/Users/lyuml-win/Desktop/building-services-agent')
(agent/'docs/evidence/reduced-branch-network.json').write_text(json.dumps(summary,indent=2))
receipt=dict(report_sha256=sha(report),html_cells_reconciled=240,rows=40,native_geometry_unchanged=True,
    source_review_sha256=sha(SOURCE/'review.json'),scope_sha256=sha(scope),check_sha256=sha(check),pressure_budget_complete=False)
(OUT/'review.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps(receipt,indent=2))

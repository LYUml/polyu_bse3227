"""Actual-branch data-only screening of pinned upstream sparse tee tables."""
import ast
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
from bsa.contraction_candidate import arrays,COMMIT,SOURCE_SHA,LICENSE_SHA
from bsa.duct_fitting_data import lookup

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
source=HERE/'raw-python-hvac-smacna.py';license_path=HERE/'raw-LICENSE-python-hvac.md'
arrays(source,license_path) # Exact previously reviewed source/license SHA gate.
tree=ast.parse(source.read_text())
def literal(class_name,name):
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==class_name)
    node=next(n.value for n in cls.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
    assert isinstance(node,ast.Call) and ast.unparse(node.func)=='np.array' and len(node.args)==1 and not node.keywords
    return ast.literal_eval(node.args[0])
vel=literal('DivergingJunctionA11N','_vb_on_vc');flow=literal('DivergingJunctionA11N','_Vb_on_Vc')
grid=literal('DivergingJunctionA11P','_zeta_b')
# Upstream 9999.9 is a missing-data sentinel, never an engineering coefficient.
table=dict(axes=[dict(quantity='outlet_to_inlet_velocity_ratio',values=vel),dict(quantity='outlet_to_inlet_flow_ratio',values=flow)],coefficients=[[None if v==9999.9 else v for v in row] for row in grid])
run=ROOT/'runs/reduced-branch-network-reviewed/one-plane-source-extension-reviewed'
record=json.loads((run/'maximum/fitting-data.json').read_text())
rows=[x for x in record['table_results'] if 'Fitting5-28,branch' in x['citation_location']]
assert len(rows)==13
results=[]
for row in rows:
    probe=lookup(table,row['native_quantities'])
    old=row['coefficient'];new=probe['coefficient']
    if old is not None:
        assert new is not None and math.isclose(old,new,rel_tol=1e-12,abs_tol=0)
    else:assert new is None
    results.append(dict(product_guid=row['product_guid'],status=probe['status'],reason=probe['reason'],previously_supported=old is not None,newly_supported=False))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
out=ROOT/'runs/upstream-sparse-tee-screen';out.mkdir(exist_ok=False)
summary=dict(upstream_commit=COMMIT,source_sha256=SOURCE_SHA,license_sha256=LICENSE_SHA,
    candidate_class='DivergingJunctionA11P',actual_branch_queries=13,bounded_values=sum(x['status']=='calculated' for x in results),
    newly_supported_paths=0,unresolved_reasons=dict(Counter(x['reason'] for x in results if x['status']!='calculated')),
    missing_sentinels_masked=True,upstream_package_executed=False,production_results_modified=False,
    physical_applicability_verified=False,design_accepted=False,method_sha256=sha(Path(__file__)))
(out/'review.json').write_text(json.dumps(dict(summary=summary,cases=results),indent=2))
print(json.dumps(summary,indent=2))

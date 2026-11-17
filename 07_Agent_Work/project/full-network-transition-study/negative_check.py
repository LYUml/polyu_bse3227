import json
from pathlib import Path
from bsa.source_fitting_data import evaluate
here=Path(__file__).resolve().parent;root=here.parents[1];basis=json.loads((here/'basis.json').read_text())
for table in basis['tables']:
 if table.get('transition_family')=='centred_equal_angle_pyramidal':table['transition_family']='centred_one_plane'
wrong=here/'negative-family-basis.json';wrong.write_text(json.dumps(basis,indent=2))
r,_=evaluate(root/'runs/source-network-analysis-native',wrong)
failed=[v for v in r['table_results'] if v.get('transition_flow_check') and v['transition_flow_check'].get('family_check')]
assert len(failed)==8 and all(v['coefficient'] is None and v['reason']=='declared transition family not met' for v in failed)
assert r['calculated_table_paths']==23 and not r['pressure_budget_complete']
(here/'negative-check.json').write_text(json.dumps(dict(incorrect_family_paths=8,all_rejected_before_lookup=True,existing_conditional_paths_preserved=23,design_accepted=False),indent=2))
print('All8 wrong-family real native queries retain null; original23 preserved')

import json,hashlib
from pathlib import Path
import ezdxf
from bsa.ifc_native import run
R=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/constant-height-tee-network');O=R/'details';p=O/'Constant Height Branch Details.dxf';d=ezdxf.readfile(p);d.layers.new('BSA_SECTION_REFERENCE')
for e in d.modelspace():
 if e.dxf.layer=='DETAIL_REFERENCE':e.dxf.layer='BSA_SECTION_REFERENCE'
d.saveas(p);sheet=json.loads((O/'sheet.json').read_text());sheet['reference_layer']='BSA_SECTION_REFERENCE';(O/'sheet.json').write_text(json.dumps(sheet,indent=2));n=run(p,O/'sheet.json',O/'native');counts={}
for e in d.modelspace():
 if e.dxf.layer=='NATIVE_SIDE_CUT':
  g=e.get_xdata('BSA_IFC')[0].value;counts[g]=counts.get(g,0)+1
cases=json.loads((R/'integration.json').read_text())['cases'];assert set(counts)=={r[k] for r in cases for k in ['tee_guid','transition_guid']};labels=[e.dxf.text for e in d.modelspace() if e.dxftype()=='TEXT' and e.dxf.text.endswith('mm')];assert len(labels)==9
(O/'projection.json').write_text(json.dumps(dict(ifc_sha256=hashlib.sha256((R/'Supply Network.ifc').read_bytes()).hexdigest(),native_product_section_counts=counts,represented_products=18,assembly_count=9,labels=labels,native_reopen_pass=n['native_reopen_pass'],visual_review='pending',design_accepted=False),indent=2));print('9native side details saved/reopened')

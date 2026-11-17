import json,hashlib
from pathlib import Path
import ezdxf
from bsa.ifc_native import run
R=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/equal-cross-compound-core-candidate');O=R/'details-readable';O.mkdir(exist_ok=False);doc=ezdxf.readfile(R/'details/Constant Junction Core Details.dxf');counts={}
for e in doc.modelspace():
 if e.dxftype()=='TEXT':e.dxf.height*=1.5;e.dxf.text=e.dxf.text.replace('1:20','1:30')
 if e.dxftype()=='LINE' and e.dxf.layer=='BSA_DETAIL_CUT':
  g=e.get_xdata('BSA_IFC')[0].value;counts[g]=counts.get(g,0)+1
p=O/'Constant Junction Core Details.dxf';doc.saveas(p);sheet=json.loads((R/'details/sheet.json').read_text());sheet['scale_denominator']=30;(O/'sheet.json').write_text(json.dumps(sheet,indent=2));n=run(p,O/'sheet.json',O/'native');(O/'projection.json').write_text(json.dumps(dict(ifc_sha256=hashlib.sha256((R/'Supply Network.ifc').read_bytes()).hexdigest(),represented_products=7,views=3,native_product_section_counts=counts,native_reopen_pass=n['native_reopen_pass'],visual_review='pending',design_accepted=False),indent=2));print('7actual bodies in3native detail views saved/reopened at1:30')

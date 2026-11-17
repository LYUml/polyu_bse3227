import json,hashlib
from pathlib import Path
import ezdxf
from bsa.ifc_native import run
R=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/equal-cross-compound-core-candidate');O=R/'drawing-pressure-reviewed';O.mkdir(exist_ok=False);doc=ezdxf.readfile(R/'drawing/Supply Network with VAV Inlets.dxf');changed=0
for e in doc.modelspace():
 if e.dxftype()=='TEXT' and 'pressure recalculation pending' in e.dxf.text:e.dxf.text='164 bodies;20outlets;114conditional values;4compound gaps;full pressure unresolved';changed+=1
assert changed==1;p=O/'Supply Network with Constant Junction Core.dxf';doc.saveas(p);sheet=json.loads((R/'drawing/sheet.json').read_text());(O/'sheet.json').write_text(json.dumps(sheet,indent=2));n=run(p,O/'sheet.json',O/'native');proj=json.loads((R/'drawing/projection.json').read_text());proj.update(native_reopen_pass=n['native_reopen_pass'],actual_PDF_visual_review='pending',header114conditional4gaps=True);(O/'projection.json').write_text(json.dumps(proj,indent=2));print('Fresh pressure-annotated164body DWG reopened')

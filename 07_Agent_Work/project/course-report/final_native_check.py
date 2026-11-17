from pathlib import Path
import hashlib,json,shutil
from bsa.native_cad import execute,lisp_string,DEFAULT_EXE
from bsa.cad_intake import export_dwg
from bsa.duct_sheet_native import compare
from bsa.cad_sheet import plot
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');R=B/'07_Agent_Work/runs/course-final-native-check';R.mkdir(exist_ok=False)
source=B/'03_Design_Drawings/Connection_Layout/Supply Air Distribution.dwg'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=sha(source);assert before=='c76a643d224889bae56ff96c91d5df160e4b75e154faf9d0829ec75749283115'
copy=R/'Supply Air Distribution.dwg';shutil.copy2(source,copy)
condition=f'(= (strcase (vl-string-translate (chr 92) "/" (strcat (getvar "DWGPREFIX") (getvar "DWGNAME")))) (strcase {lisp_string(copy)}))'
scr=R/'save.scr';scr.write_text(f'(if {condition} (command "_.QSAVE") (princ "BSA WRONG DOCUMENT"))\n_.QUIT\n_Y\n',encoding='ascii')
execute(DEFAULT_EXE,copy,scr,R/'save.log',120)
dxf=export_dwg(copy,R/'reopened',DEFAULT_EXE)
spec=json.loads((B/'07_Agent_Work/project/bse3227-flow-direction-inputs/native.json').read_text(encoding='utf-8'))
reference=B/'07_Agent_Work/runs/vav-recenter-friction-compensated/delivery/native/reopened/source-export.dxf'
geometry=compare(reference,dxf,spec['layers'])
plotted=plot(copy,dxf,spec['sheet'],R/'Supply Air Distribution.pdf',DEFAULT_EXE)
assert sha(source)==before
result={'original_dwg_sha256':before,'saved_copy_dwg_sha256':sha(copy),'native_export_sha256':sha(dxf),'native_geometry':geometry,'plot':plotted,'source_unchanged':True,'visual_review':'pending','design_accepted':False}
(R/'review.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))

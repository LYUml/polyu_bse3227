"""Isolated AutoCAD 2027 Core Console operations; never touch a live user session."""
from pathlib import Path
import hashlib, subprocess, re

ROOT = Path(__file__).resolve().parents[2]
CORE = Path('C:/Program Files/Autodesk/AutoCAD 2027/accoreconsole.exe')
CACHE = ROOT/'05_Calculations/.cache'
CACHE.mkdir(exist_ok=True)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def run(dwg, expressions, name, allow_write=False):
    dwg=Path(dwg).resolve()
    if allow_write:
        assert dwg.is_relative_to(ROOT/'05_Calculations') or dwg.is_relative_to(ROOT/'03_Design_Drawings')
    before=sha(dwg)
    # Verify the native document before any caller-supplied write operation.
    guard=f'(if (/= (strcase (strcat (getvar "DWGPREFIX") (getvar "DWGNAME"))) (strcase "{dwg.as_posix()}")) (princ "PATH_CHECK_NEEDS_NORMALIZATION"))'
    # AutoCAD returns backslashes. Normalize before comparison; quit on mismatch.
    guard=f'(if (/= (strcase (vl-string-translate "\\\\" "/" (strcat (getvar "DWGPREFIX") (getvar "DWGNAME")))) (strcase "{dwg.as_posix()}")) (progn (princ "WRONG_DOCUMENT_ABORT") (quit)))'
    script=CACHE/f'{name}.scr'
    script.write_text('\n'.join([guard,'(setvar "FILEDIA" 0)','(setvar "CMDECHO" 0)',*expressions,f'(princ "{name.upper()}_COMPLETE")','(princ)'])+'\n',encoding='ascii')
    result=subprocess.run([str(CORE),'/i',str(dwg),'/s',str(script),'/l','en-US'],capture_output=True,timeout=180)
    log=result.stdout.decode('utf-16le',errors='replace')
    (CACHE/f'{name}.log').write_text(log,encoding='utf8')
    assert result.returncode==0 and f'{name.upper()}_COMPLETE' in log, log[-3000:]
    assert not re.search(r'^WRONG_DOCUMENT_ABORT',log,re.M) and '; error:' not in log.lower(),log[-3000:]
    if not allow_write: assert sha(dwg)==before,'Read-only operation modified input'
    return log

if __name__=='__main__':
    import shutil,json,ezdxf
    source=ROOT/'01_Assignment_Brief/Building_Drawings/Project layout.dwg'
    work=CACHE/'source_read.dwg'; shutil.copy2(source,work)
    out=CACHE/'source.dxf'
    if out.exists():out.unlink()
    run(work,[f'(command "_.DXFOUT" "{out.as_posix()}" "16")'],'source_export')
    d=ezdxf.readfile(out)
    from collections import Counter
    info={'source_sha256':sha(source),'units':d.units,'origin_mm':[64345.93225182503,15925.58365525945],
          'outer_dimensions_mm':[45000,30000],'source_area_label_m2':1022,
          'model_entities':len(d.modelspace()),'entity_types':dict(Counter(e.dxftype() for e in d.modelspace())),
          'source_layouts':[l.name for l in d.layouts],
          'evidence':'AutoCAD 2027 native export; geometry from unmodified source. DXF is an inspection intermediate, not DWG fidelity acceptance.'}
    (ROOT/'05_Calculations/data/source_geometry.json').write_text(json.dumps(info,indent=2))
    print(json.dumps(info,indent=2))

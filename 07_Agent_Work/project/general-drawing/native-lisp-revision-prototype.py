"""Bounded native DWG text revisions with whole-entity preservation checks."""
import json
import math
from pathlib import Path
import shutil

import ezdxf
from ezdxf.lldxf.tagwriter import TagCollector

from . import drawing_document, workspace
from .cli import digest
from .native_cad import execute,lisp_string
from .cad_intake import export_dwg
from .cad_sheet import plot


def configuration(project):
    project=Path(project).resolve()
    if not workspace.allowed(project):raise ValueError('Host project workspace required')
    raw=project.read_bytes();data=json.loads(raw.decode('utf-8-sig'))
    if not isinstance(data,dict) or set(data)!={'schema','source','drawing','drawing_sha256','edits','sheet'} or data['schema']!='bsa.drawing-revision/1':
        raise ValueError('Exact drawing-revision fields required')
    drawing_document.text(data['source'])
    if not isinstance(data['drawing'],str) or Path(data['drawing']).is_absolute():raise ValueError('Recipe-relative existing DWG required')
    source=(project.parent/data['drawing']).resolve()
    if not workspace.allowed(source) or source.suffix.lower()!='.dwg' or digest(source)!=data['drawing_sha256']:
        raise ValueError('Drawing source escaped workspace or changed')
    if not isinstance(data['edits'],list) or not data['edits']:raise ValueError('Explicit nonempty edits required')
    seen=set()
    for e in data['edits']:
        if set(e)!={'handle','expected','replacement'} or not isinstance(e['handle'],str) or not e['handle'] or any(c not in '0123456789ABCDEFabcdef' for c in e['handle']):
            raise ValueError('Explicit hexadecimal TEXT handle required')
        if e['handle'].upper() in seen:raise ValueError('Duplicate edit target')
        seen.add(e['handle'].upper())
        if set(e['expected'])!={'text','layer','insert'} or set(e['replacement'])!={'text','insert'}:raise ValueError('Exact before/after text and insertion fields required')
        drawing_document.text(e['expected']['layer'])
        for values in (e['expected'],e['replacement']):
            drawing_document.text(values['text']);drawing_document.point(values['insert'])
            if not values['text'].isascii():raise ValueError('Current native text revision requires ASCII; Unicode not verified')
    return data,source,raw


def revised(doc,edits):
    for e in edits:
        obj=doc.entitydb.get(e['handle'].upper());expected=e['expected']
        if obj is None or obj.dxftype()!='TEXT' or obj.dxf.layer!=expected['layer'] or obj.dxf.text!=expected['text']:
            raise ValueError('TEXT target/type/layer/content precondition failed')
        if obj.get_layout().name!='Model' or doc.layers.get(obj.dxf.layer).is_locked() or obj.dxf.paperspace or obj.dxf.halign or obj.dxf.valign or not all(math.isclose(obj.dxf.insert[i],expected['insert'][i],abs_tol=1e-8,rel_tol=0) for i in range(2)):
            raise ValueError('Unaligned model-space TEXT insertion precondition required')
    for e in edits:
        obj=doc.entitydb[e['handle'].upper()];obj.dxf.text=e['replacement']['text']
        obj.dxf.insert=(*e['replacement']['insert'],obj.dxf.insert.z)
    return doc


def snapshot(doc):
    """Literal supported DXF serialization, including block and paper entities."""
    if any(b.block.dxf.flags&12 for b in doc.blocks):raise ValueError('External references need separate packaging')
    records={'units':int(doc.header.get('$INSUNITS',0))}
    def tags(e):return repr(TagCollector.dxftags(e))
    for layout in doc.layouts:
        for e in layout:records['entity:'+e.dxf.handle]=(layout.name,tags(e))
    for block in doc.blocks:
        if not block.is_any_layout:
            for e in block:records['block:'+e.dxf.handle]=(block.name,tags(e))
    for name in ('layers','styles','linetypes','dimstyles'):
        for e in getattr(doc,name):records[name+':'+e.dxf.name]=tags(e)
    return records


def compare(before,actual,edits):
    wanted=snapshot(revised(ezdxf.readfile(before),edits));saved=snapshot(ezdxf.readfile(actual))
    if wanted!=saved:
        differences=[k for k in wanted.keys()|saved.keys() if wanted.get(k)!=saved.get(k)]
        raise ValueError('Native revision differs outside approved changes: '+str(differences[:8]))
    return dict(preserved_records=len(wanted),edited_texts=len(edits),blocks_and_paper_entities_preserved=True,
                scope='Literal saved entity/block/paper and layer/style records; unexamined dictionaries/product semantics and visual acceptance remain separate')


def methods():
    return {name:digest(Path(__file__).with_name(name)) for name in ('drawing_revision.py','drawing_document.py','native_cad.py','cad_intake.py','cad_sheet.py')}


def balanced_lisp(value):
    depth=0;quoted=False;escaped=False
    for c in value:
        if quoted:
            if escaped:escaped=False
            elif c=='\\':escaped=True
            elif c=='"':quoted=False
        elif c=='"':quoted=True
        elif c=='(':depth+=1
        elif c==')':
            depth-=1
            if depth<0:return False
    return depth==0 and not quoted


def script_text(data,copied,target,expected):
    condition=f'(= (strcase (vl-string-translate (chr 92) "/" (strcat (getvar "DWGPREFIX") (getvar "DWGNAME")))) (strcase {lisp_string(copied)}))'
    checks=[];changes=[]
    for e in data['edits']:
        handle=lisp_string(e['handle']);old=e['expected'];new=e['replacement'];z=expected.entitydb[e['handle'].upper()].dxf.insert.z
        checks.append(f'(and (setq e (handent {handle})) (setq d (entget e)) (= (cdr (assoc 0 d)) "TEXT") (= (cdr (assoc 410 d)) "Model") (= (cdr (assoc 1 d)) {lisp_string(old["text"])}) (= (cdr (assoc 8 d)) {lisp_string(old["layer"])}) (equal (cdr (assoc 10 d)) (list {old["insert"][0]:.17g} {old["insert"][1]:.17g} {z:.17g}) 1e-8))')
        changes.append(f'(setq e (handent {handle}) d (entget e)) (setq d (subst (cons 1 {lisp_string(new["text"])}) (assoc 1 d) d)) (setq d (subst (cons 10 (list {new["insert"][0]:.17g} {new["insert"][1]:.17g} (caddr (cdr (assoc 10 d))))) (assoc 10 d) d)) (entmod d) (entupd e)')
    expression=f'(if (and {condition} '+ ' '.join(checks)+') (progn (setvar "FILEDIA" 0) (setvar "CMDDIA" 0) '+' '.join(changes)+f' (command "_.SAVEAS" "2018" {lisp_string(target)})) (princ "BSA REVISION PRECONDITION FAILED"))'
    if not balanced_lisp(expression):raise ValueError('Unbalanced generated revision expression')
    return expression+'\n_.QUIT\n_Y\n'


def verify(project,out):
    project,out=Path(project).resolve(),Path(out).resolve()
    if not workspace.intake_output(out):raise ValueError('Host project workspace required')
    data,source,_=configuration(project);record=json.loads((out/'revision-result.json').read_text(encoding='utf-8'))
    if record['project_sha256']!=digest(project) or record['methods']!=methods() or record['design_accepted'] is not False:raise ValueError('Revision source/method/acceptance changed')
    if digest(out/'source/source-copy.dwg')!=digest(source):raise ValueError('Original DWG copy changed')
    for name,sha in record['artifacts'].items():
        path=(out/name).resolve()
        if not path.is_relative_to(out) or digest(path)!=sha:raise ValueError('Revision artifact changed or escaped')
    checked=compare(out/'source/source-export.dxf',out/'reopened/source-export.dxf',data['edits'])
    if checked!=record['preservation']:raise ValueError('Revision preservation record differs')
    return dict(integrity_pass=True,native_reopen_pass=True,preservation=checked,
                artifacts=[dict(path=name,sha256=record['artifacts'][name]) for name in ('Revised Drawing.dwg','Revised Drawing.pdf')],
                visual_review='pending',design_accepted=False)


def run(project,out,*,autocad):
    project,out,exe=Path(project).resolve(),Path(out).resolve(),Path(autocad).resolve()
    data,source,raw=configuration(project)
    if not workspace.intake_output(out) or out.exists() or any(out==p or out in p.parents for p in (project,source,exe)) or not exe.is_file():raise ValueError('Fresh isolated output and host AutoCAD required')
    pins=methods();exe_sha=digest(exe);out.mkdir(parents=True)
    before=export_dwg(source,out/'source',exe)
    expected=revised(ezdxf.readfile(before),data['edits']);snapshot(expected);expected.saveas(out/'expected.dxf')
    copied=out/'working.dwg';shutil.copyfile(source,copied);target=out/'Revised Drawing.dwg'
    script=out/'revise.scr'
    # Load source as AutoLISP rather than passing long text/semicolon-bearing
    # literals through the command-script reader.
    program=out/'revision.lsp'
    program.write_text(script_text(data,copied,target,expected).split('\n')[0]+'\n',encoding='ascii')
    script.write_text(f'(load {lisp_string(program)})\n_.QUIT\n_Y\n',encoding='ascii')
    execute(exe,copied,script,out/'revise.log',120)
    if not target.is_file():raise ValueError('Native revision did not create approved output')
    exported=export_dwg(target,out/'reopened',exe);preserved=compare(before,exported,data['edits'])
    plotted=plot(target,exported,data['sheet'],out/'Revised Drawing.pdf',exe)
    if project.read_bytes()!=raw or digest(source)!=data['drawing_sha256'] or digest(exe)!=exe_sha or methods()!=pins:raise ValueError('Revision input/runtime/method changed')
    names=['source/source-copy.dwg','source/source-export.dxf','reopened/source-export.dxf','Revised Drawing.dwg','Revised Drawing.pdf']
    record=dict(project_sha256=digest(project),source_sha256=digest(source),methods=pins,autocad_sha256=exe_sha,preservation=preserved,plot=plotted,
                artifacts={name:digest(out/name) for name in names},native_reopen_pass=True,design_accepted=False)
    (out/'revision-result.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    return verify(project,out)

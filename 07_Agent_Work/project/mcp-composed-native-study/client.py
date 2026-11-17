import asyncio,base64,hashlib,json,os,shutil,sys
from pathlib import Path
from datetime import timedelta
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
root=Path(r'C:\Users\lyuml-win\Desktop\polyu_bse3227');here=Path(__file__).resolve().parent
async def main():
 renderer=shutil.which('pdftoppm');assert renderer
 params=StdioServerParameters(command=sys.executable,args=['-m','bsa.mcp_server','--autocad',r'C:\Program Files\Autodesk\AutoCAD 2027\accoreconsole.exe','--pdftoppm',renderer],cwd=str(Path.cwd()),env={**os.environ,'BSA_PROJECT_ROOT':str(root)})
 async with stdio_client(params) as streams:
  async with ClientSession(*streams) as session:
   await session.initialize()
   async def call(name,args):
    r=await session.call_tool(name,args,read_timeout_seconds=timedelta(seconds=1200));assert not r.isError,str(r);return r
   out='07_Agent_Work/runs/mcp-composed-native-delivery'
   response=await call('bsa_run_native_network_delivery',dict(source='07_Agent_Work/runs/source-network-analysis-native',out=out));run=response.structuredContent
   assert run['product_count']==102 and run['original_requirement_count']==33 and run['native_reopen_pass'] and run['pdf_reference_pass'] and not run['design_accepted']
   (here/'execution-summary.json').write_text(json.dumps(run,indent=2));print('Actual MCP composed native delivery finished:102 products,33 requirements, DWG/PDF checks pass',flush=True)
   response=await call('bsa_inspect_native_network_delivery',dict(out=out));checked=response.structuredContent
   assert checked['integrity_pass'] and {k:v for k,v in checked.items() if k!='integrity_pass'}==run
   (here/'inspection-summary.json').write_text(json.dumps(checked,indent=2));print('Independent MCP native/source/layout/PDF reconstruction agrees',flush=True)
   pdf=next(a for a in run['artifacts'] if a['project_path'].endswith('.pdf'))
   response=await call('bsa_render_source_page',dict(source=pdf['project_path'],page=1,out='07_Agent_Work/runs/mcp-composed-native-page'))
   meta=response.structuredContent;assert meta['source_sha256']==pdf['sha256'];png=base64.b64decode(next(c for c in response.content if c.type=='image').data);assert hashlib.sha256(png).hexdigest()==meta['image_sha256']
   (here/'Rendered Sheet.png').write_bytes(png);(here/'page-summary.json').write_text(json.dumps(meta,indent=2));print('MCP PDF page returned; source and image hashes agree',flush=True)
asyncio.run(main())

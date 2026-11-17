import asyncio,json,os,sys
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
here=Path(__file__).resolve().parent;root=Path(r'C:\Users\lyuml-win\Desktop\polyu_bse3227')
async def main():
 prior=json.loads((here/'summary.json').read_text());base=dict(out='07_Agent_Work/runs/mcp-native-fitting-analysis',record_sha256=prior['record_sha256'])
 params=StdioServerParameters(command=sys.executable,args=['-m','bsa.mcp_server'],cwd=str(Path.cwd()),env={**os.environ,'BSA_PROJECT_ROOT':str(root)})
 async with stdio_client(params) as streams:
  async with ClientSession(*streams) as session:
   await session.initialize();rows=[];offset=0
   while True:
    r=await session.call_tool('bsa_list_native_fitting_requests',dict(**base,offset=offset));assert not r.isError;page=r.structuredContent;rows+=page['requests']
    if page['next_offset'] is None:break
    offset=page['next_offset']
   assert len(rows)==76
   target=next(r for r in rows if r['predefined_type']=='TRANSITION' and r['status']=='physical_review_required')
   r=await session.call_tool('bsa_read_native_fitting_request',dict(**base,**{k:target[k] for k in ('product_guid','inlet_port_guid','outlet_port_guid')}));assert not r.isError and r.structuredContent['transition_end_straight_study']
   for bad in (True,'2',21,0):
    r=await session.call_tool('bsa_list_native_fitting_requests',dict(**base,limit=bad));assert r.isError
   (here/'final-reader-summary.json').write_text(json.dumps(dict(requests_read=76,transition_detail_read=True,invalid_limit_values_rejected=4,record_sha256=base['record_sha256'],source_inspection='Prior actual inspection; unchanged saved bytes enforced during reads',design_accepted=False),indent=2));print('Final reader:all76 identities, transition details and4 invalid limits verified')
asyncio.run(main())

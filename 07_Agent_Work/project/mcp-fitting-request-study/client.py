import asyncio,json,os,sys
from pathlib import Path
from datetime import timedelta
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
root=Path(r'C:\Users\lyuml-win\Desktop\polyu_bse3227');here=Path(__file__).resolve().parent
async def main():
 params=StdioServerParameters(command=sys.executable,args=['-m','bsa.mcp_server'],cwd=str(Path.cwd()),env={**os.environ,'BSA_PROJECT_ROOT':str(root)})
 async with stdio_client(params) as streams:
  async with ClientSession(*streams) as session:
   await session.initialize()
   async def call(name,args):
    r=await session.call_tool(name,args,read_timeout_seconds=timedelta(seconds=1200));assert not r.isError,str(r);return r.structuredContent
   out='07_Agent_Work/runs/mcp-native-fitting-analysis';checked=await call('bsa_inspect_native_fitting_analysis',dict(out=out));assert checked['integrity_pass'];sha=checked['artifacts'][0]['sha256'];base=dict(out=out,record_sha256=sha)
   print('Fresh native/source inspection completed; reading paginated requests',flush=True)
   rows=[];offset=0;pages=0
   while True:
    page=await call('bsa_list_native_fitting_requests',dict(**base,offset=offset));rows+=page['requests'];pages+=1
    if page['next_offset'] is None:break
    offset=page['next_offset']
   assert len(rows)==76 and len({(r['product_guid'],r['inlet_port_guid'],r['outlet_port_guid']) for r in rows})==76
   details=[]
   for status in ('physical_review_required','source_data_required','table_support_missing'):
    page=await call('bsa_list_native_fitting_requests',dict(**base,status=status));row=page['requests'][0]
    detail=await call('bsa_read_native_fitting_request',dict(**base,**{k:row[k] for k in ('product_guid','inlet_port_guid','outlet_port_guid')}));assert detail['request']['status']==status and not detail['design_accepted'];details.append(detail)
   row=next(r for r in rows if r['predefined_type']=='TRANSITION' and r['status']=='physical_review_required')
   detail=await call('bsa_read_native_fitting_request',dict(**base,**{k:row[k] for k in ('product_guid','inlet_port_guid','outlet_port_guid')}));assert detail['request']['transition_geometry'] and len(detail['transition_end_straight_study'])==1;details.append(detail)
   bad=await session.call_tool('bsa_list_native_fitting_requests',dict(out=out,record_sha256='0'*64));assert bad.isError
   (here/'details.json').write_text(json.dumps(details,indent=2));(here/'summary.json').write_text(json.dumps(dict(pages=pages,requests=len(rows),detail_reads=len(details),all_three_statuses_preserved=True,transition_geometry_and_straight_study_read=True,wrong_record_hash_rejected=True,source_inspection_integrity_pass=True,record_sha256=sha,design_accepted=False),indent=2));print('76 directed requests across4 pages;4 detailed reads and wrong-hash rejection pass',flush=True)
asyncio.run(main())

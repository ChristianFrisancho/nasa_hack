import json,sys
s=open(sys.argv[1]).read(); d=json.loads(s[s.find('{'):s.rfind('}')+1])
for r in d.get('results',[]):
    print('##',r.get('url')); print((r.get('title') or '')[:120]); print((r.get('content') or r.get('raw_content') or '')[:int(sys.argv[2]) if len(sys.argv)>2 else 500].replace('\n',' ')); print()

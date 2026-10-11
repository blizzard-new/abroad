import ast, hashlib, json, resource, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from exchange_info import ncu_student_view as module

mode=sys.argv[1]
if mode=='old':
    text=subprocess.check_output(['git','show','b2aaee8f7cc770a550d18b19a9f213d34cccd978:src/exchange_info/ncu_student_view.py'],text=True)
    tree=ast.parse(text);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='ncu_processed_pages')
    scope=vars(module).copy();exec(compile(ast.Module(body=[node],type_ignores=[]),'<exact-pre-streaming-reader>','exec'),scope)
    reader=scope['ncu_processed_pages']
else:reader=module.ncu_processed_pages
with ThreadPoolExecutor(max_workers=4) as pool: batches=list(pool.map(lambda _:reader(),range(4)))
peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024
hashes=[]
for rows in batches:
    digest=hashlib.sha256()
    for row in rows:digest.update(json.dumps(row.model_dump(mode='json'),ensure_ascii=False,sort_keys=True).encode())
    hashes.append(digest.hexdigest())
print(json.dumps({'mode':mode,'scope':'four concurrent NCU source-page reads only; not full-app acceptance','rows_per_read':len(batches[0]),'peak_rss_mib_before_hashing':peak,'all_output_hashes_identical':len(set(hashes))==1,'rows_hash':hashes[0]}))

from pathlib import Path
import ast
for p in Path('tests').glob('test_*.py'):
 s=p.read_text(); tree=ast.parse(s); lines=s.splitlines(keepends=True); offsets=[0]
 for line in lines:offsets.append(offsets[-1]+len(line))
 def span(n):
  # AST columns are UTF-8 byte offsets, convert to character offsets.
  return offsets[n.lineno-1]+len(lines[n.lineno-1].encode()[:n.col_offset].decode()), offsets[n.end_lineno-1]+len(lines[n.end_lineno-1].encode()[:n.end_col_offset].decode())
 edits=[]
 for node in ast.walk(tree):
  if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute) or node.func.attr!='setattr':continue
  targets=[n for n in node.args[:-1] if isinstance(n,ast.Constant) and isinstance(n.value,str) and (n.value=='exchange_info.api.fetch_partner_universities' or n.value=='fetch_partner_universities')]
  if not targets:continue
  # student_view direct parser tests deliberately stay unchanged.
  if len(node.args)==3 and isinstance(node.args[0],ast.Constant):continue
  target=targets[0];a,b=span(target);edits.append((a,b,repr(target.value.replace('fetch_partner_universities','create_cgu_catalogue'))))
  n=node.args[-1];a,b=span(n);edits.append((a,b,'fixed_cgu_catalogue('+s[a:b]+')'))
 if edits:
  for a,b,t in sorted(edits,reverse=True):s=s[:a]+t+s[b:]
  # Insert after future imports, or before the first actual import.
  tree=ast.parse(s);idx=next((n.lineno-1 for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom)) and not (isinstance(n,ast.ImportFrom) and n.module=='__future__')),0)
  lines=s.splitlines(keepends=True);lines.insert(idx,'from cgu_catalogue_fixture import fixed_cgu_catalogue\n');p.write_text(''.join(lines))
p=Path('tests/test_ccu_followup_validation.py');s=p.read_text().replace('    monkeypatch.setattr(api, collector, lambda: [partner])','    if collector == "fetch_partner_universities":\n        from cgu_catalogue_fixture import fixed_cgu_catalogue\n        monkeypatch.setattr(api, "create_cgu_catalogue", fixed_cgu_catalogue(lambda: [partner]))\n    else:\n        monkeypatch.setattr(api, collector, lambda: [partner])');p.write_text(s)
p=Path('tests/e2e/conftest.py');s=p.read_text();s=s.replace('original_fetch = api_module.fetch_partner_universities','original_fetch = api_module.create_cgu_catalogue');s=s.replace('api_module.fetch_partner_universities = lambda: partners','from cgu_catalogue_fixture import fixed_cgu_catalogue\n    api_module.create_cgu_catalogue = fixed_cgu_catalogue(lambda: partners)');s=s.replace('api_module.fetch_partner_universities = original_fetch','api_module.create_cgu_catalogue = original_fetch');p.write_text(s)
p=Path('src/exchange_info/static/app.js');s=p.read_text().replace('$("#partner-count").textContent = "來源暫不可用"','$("#partner-result-count").textContent = "來源暫不可用"');p.write_text(s)

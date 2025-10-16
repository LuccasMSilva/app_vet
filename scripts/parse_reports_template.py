from jinja2 import Environment
import re, sys
p = r"c:\Users\User\Desktop\i9bilder\MVP\app_vet\M Cadastro vet2.py"
with open(p, 'r', encoding='utf-8') as f:
    s = f.read()
m = re.search(r'template\s*=\s*"""(.*?)"""', s, re.S)
if not m:
    print('Could not find template string')
    sys.exit(1)

tpl = m.group(1)
print('--- Template lines ---')
for i, line in enumerate(tpl.splitlines(), start=1):
    print(f"{i:03}: {line}")

print('\n--- Parsing with Jinja2 ---')
env = Environment()
try:
    env.parse(tpl)
    print('Template parsed OK')
except Exception as e:
    import traceback
    traceback.print_exc()
    print('Error:', e)

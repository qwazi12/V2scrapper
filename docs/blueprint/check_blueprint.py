"""Static consistency validator; cannot replace a real PostgreSQL migration or OpenAPI tooling test.
Run: python check_blueprint.py
"""
import re
import sys
from pathlib import Path
import yaml

root=Path(__file__).resolve().parent
mandatory=['00_START_HERE.md','01_PRODUCT_REQUIREMENTS.md','02_ARCHITECTURE_AND_WORKFLOWS.md','03_DATABASE_SCHEMA.sql','04_OPENAPI.yaml','05_RESEARCH_AND_AI.md','06_MEDIA_AND_CONTENT.md','07_SOCIAL_ANALYTICS_AND_GROWTH.md','08_SECURITY_INFRA_OPERATIONS.md','09_TEST_STRATEGY.md','10_DELIVERY_BACKLOG.md','11_CODEX_BOOTSTRAP.md','12_CONTRACTS_AND_DECISIONS.md','13_CONFIGURATION_DEFAULTS.yaml']
errors=[]
for f in mandatory:
 p=root/f
 if not p.is_file() or p.stat().st_size<1000:errors.append(f'file missing or empty: {f}')
api=yaml.safe_load((root/'04_OPENAPI.yaml').read_text())
conf=yaml.safe_load((root/'13_CONFIGURATION_DEFAULTS.yaml').read_text())
if api.get('openapi')!='3.1.0': errors.append('OpenAPI version incorrect')
if 'paths' not in api or len(api['paths'])<75:errors.append('OpenAPI too sparse')
if 'schemas' not in api.get('components',{}):errors.append('No API schemas')

def scan(obj):
 if isinstance(obj,dict):
  for k,v in obj.items():
   if k=='$ref' and isinstance(v,str) and v.startswith('#/components/schemas/') and v.split('/')[-1] not in api['components']['schemas']:
    errors.append('bad ref: '+v)
   scan(v)
 elif isinstance(obj,list):
  for e in obj:scan(e)
scan(api)
for path,ops in api['paths'].items():
 for method,o in ops.items():
  if 'operationId' not in o:errors.append(f'missing operation ID {method} {path}')
  if 'responses' not in o:errors.append(f'missing responses {method} {path}')
  if not (path.startswith('/health/') or path in ['/api/v1/auth/oidc/start','/api/v1/auth/oidc/callback','/api/v1/social/oauth/{provider}/callback']) and not o.get('security'):
   errors.append(f'unauthenticated app route {path}')
  if method in ('post','put','patch','delete') and path not in ['/api/v1/auth/logout']:
   if 'X-CSRF-Token' not in [v.get('name') for v in o.get('parameters',[])]: errors.append(f'CSRF parameter absent {method} {path}')
for k in ['local','ci','staging','production']:
 if conf.get('environments',{}).get(k,{}).get('live_publish_allowed') is not False:errors.append(f'default live publish enabled {k}')
if conf['project']['old_project_forbidden'] != 'qwazi12/scrapper':errors.append('old project isolation check missing')
if sum(conf['strategic_scoring']['weights'].values())!=1.0:errors.append('weights do not sum to 1')
sql=(root/'03_DATABASE_SCHEMA.sql').read_text()
if 'BEGIN;' not in sql or 'COMMIT;' not in sql:errors.append('SQL transaction bound missing')
tables=re.findall(r'^CREATE TABLE\s+([a-z_]+)',sql,re.M)
if len(tables)<40:errors.append('core schema too sparse')
if len(tables)!=len(set(tables)):errors.append('duplicate SQL tables')
for table in re.findall(r'REFERENCES\s+([a-z_]+)\(',sql):
 if table not in tables:errors.append('missing SQL referenced table '+table)
requirements=(root/'01_PRODUCT_REQUIREMENTS.md').read_text()
acceptance=(root/'09_TEST_STRATEGY.md').read_text()
backlog=(root/'10_DELIVERY_BACKLOG.md').read_text()
for i in range(1,31):
 if f'FR-{i:03}' not in requirements:errors.append(f'FR-{i:03} missing')
for i in range(1,61):
 if f'AT-{i:03}' not in acceptance:errors.append(f'AT-{i:03} missing')
if 'SCOS-104' not in backlog:errors.append('last autonomy milestone missing')
if 'idx_one_confirmed_publication' not in sql:errors.append('confirmed publication uniqueness missing')
print(f'files={len(mandatory)} api_paths={len(api["paths"])} operations={sum(len(v) for v in api["paths"].values())} schemas={len(api["components"]["schemas"])} postgres_tables={len(tables)} FR=30 AT=60')
if errors:
 for e in errors:print('ERROR:',e)
 sys.exit(1)
print('STATIC BLUEPRINT CHECKS PASS. NOTE: PostgreSQL DDL execution and OpenAPI runtime parity remain implementation-stage tests.')

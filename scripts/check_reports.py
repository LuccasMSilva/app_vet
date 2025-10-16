import os, sqlite3
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
db_path = os.path.join(basedir, 'instance', 'pets.db')
print('DB:', db_path)
if not os.path.exists(db_path):
    print('No DB found')
    raise SystemExit(1)
conn = sqlite3.connect(db_path)
c = conn.cursor()
print('\n-- users (id, username, role, clinic_id) --')
for row in c.execute('select id, username, role, clinic_id from user'):
    print(row)

print('\n-- clinics (id, name, contact) --')
for row in c.execute('select id, name, contact from clinic'):
    print(row)

print('\n-- completed animals grouped by clinic_id --')
for row in c.execute("select clinic_id, count(*) from animal where status='Concluído' group by clinic_id"):
    print(row)

print('\n-- completed animals details --')
for row in c.execute("select id, nome, status, dono_id, clinic_id, data_agendamento from animal where status='Concluído'"):
    print(row)

conn.close()

import os, sqlite3
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
db_path = os.path.join(basedir, 'instance', 'pets.db')
print('DB:', db_path)
if not os.path.exists(db_path):
    print('No DB found')
    raise SystemExit(1)
conn = sqlite3.connect(db_path)
c = conn.cursor()
# For each user with role=clinic, find Clinic with same name and set user.clinic_id
for uid, uname in c.execute("select id, username from user where role='clinic'"):
    r = c.execute('select id from clinic where name=?', (uname,)).fetchone()
    if r:
        clinic_id = r[0]
        print('Setting user', uid, 'clinic_id ->', clinic_id)
        c.execute('update user set clinic_id=? where id=?', (clinic_id, uid))
conn.commit()
# Re-run the reports check
for row in c.execute("select clinic_id, count(*) from animal where status='Concluído' group by clinic_id"):
    print('completed per clinic:', row)
conn.close()

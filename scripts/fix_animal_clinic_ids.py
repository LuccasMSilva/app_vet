import os, sqlite3
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
db_path = os.path.join(basedir, 'instance', 'pets.db')
print('DB:', db_path)
if not os.path.exists(db_path):
    print('No DB found')
    raise SystemExit(1)
conn = sqlite3.connect(db_path)
c = conn.cursor()
# For each user with role=clinic, update animals that have clinic_id equal to the user's id
for uid, uname in c.execute("select id, username from user where role='clinic'"):
    # find clinic id with the same name
    r = c.execute('select id from clinic where name=?', (uname,)).fetchone()
    if r:
        clinic_id = r[0]
        print(f'User {uid} ({uname}) -> clinic {clinic_id}')
        res = c.execute('update animal set clinic_id=? where clinic_id=? and status!=? ', (clinic_id, uid, 'Concluído'))
        print('Updated rows:', conn.total_changes)
# For completed animals, also update if still pointing to a user id
for uid, uname in c.execute("select id, username from user where role='clinic'"):
    r = c.execute('select id from clinic where name=?', (uname,)).fetchone()
    if r:
        clinic_id = r[0]
        c.execute('update animal set clinic_id=? where clinic_id=?', (clinic_id, uid))
conn.commit()
print('Done')
conn.close()

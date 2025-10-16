import os
from sqlalchemy import create_engine, text

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
db_path = os.path.join(basedir, 'instance', 'pets.db')
print('Using DB:', db_path := os.path.abspath(db_path))
if not os.path.exists(db_path):
    print('Database not found, aborting.')
    raise SystemExit(1)

engine = create_engine(f"sqlite:///{db_path}")
with engine.connect() as conn:
    trans = conn.begin()
    try:
        # Find clinic users
        users = conn.execute(text("SELECT id, username, contact FROM user WHERE role='clinic'"))
        created = []
        for u in users:
            uid = u[0]
            uname = u[1]
            ucontact = u[2] or ''
            # Check if clinic exists with same name
            r = conn.execute(text("SELECT id FROM clinic WHERE name = :name"), {'name': uname}).fetchone()
            if r:
                clinic_id = r[0]
                print(f'Clinic already exists for user {uname} -> clinic_id {clinic_id}')
            else:
                res = conn.execute(text("INSERT INTO clinic (name, contact) VALUES (:name, :contact)"), {'name': uname, 'contact': ucontact})
                clinic_id = conn.execute(text('SELECT last_insert_rowid()')).scalar()
                created.append((uid, clinic_id))
                print(f'Created clinic {clinic_id} for user {uname}')
            # Update user.clinic_id if not set
            conn.execute(text('UPDATE user SET clinic_id = :cid WHERE id = :uid AND (clinic_id IS NULL OR clinic_id = 0)'), {'cid': clinic_id, 'uid': uid})
            # Update animals that referenced the user.id as clinic_id -> new clinic_id
            conn.execute(text('UPDATE animal SET clinic_id = :cid WHERE clinic_id = :uid'), {'cid': clinic_id, 'uid': uid})

        trans.commit()
        print('Migration committed. Created clinics:', created)
    except Exception as e:
        print('Migration failed:', e)
        trans.rollback()
        raise

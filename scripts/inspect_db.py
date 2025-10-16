import sqlite3, os
p = os.path.join(os.path.dirname(__file__), '..', 'instance', 'pets.db')
print('db path:', os.path.abspath(p))
print('exists:', os.path.exists(p))
if not os.path.exists(p):
    print('Database not created yet')
else:
    conn = sqlite3.connect(p)
    c = conn.cursor()
    try:
        print('\n-- users --')
        for row in c.execute('select id, username, role, email from user'):
            print(row)
    except Exception as e:
        print('error reading users:', e)
    try:
        print('\n-- animals --')
        for row in c.execute('select id, nome, status, dono_id, clinic_id, data_agendamento, verification_token, token_validated from animal'):
            print(row)
    except Exception as e:
        print('error reading animals:', e)
    conn.close()

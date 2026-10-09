import sqlite3
conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cur.fetchall()
print('Tables:', tables)
try:
    cur.execute("SELECT COUNT(*) FROM translator_signvocabulary;")
    print('Vocab count:', cur.fetchone()[0])
except Exception as e:
    print('Vocab count error:', e)
conn.close()

import requests
import sqlite3

baseUrl = 'http://127.0.0.1:5050'

# 1. Test load sample data
r = requests.post(baseUrl + '/api/load-sample-data')
assert r.status_code == 200, f"Error: {r.text}"
data = r.json()
print('ETL Process Status:', r.status_code)
print('DB Result from API:', data.get('db_result'))
print('Total Audit Rules:', len(data['audit_logs']))

# 2. Test download SQLite database
r_db = requests.get(baseUrl + '/api/download-db')
assert r_db.status_code == 200
print('Download DB Status:', r_db.status_code, 'Content-Type:', r_db.headers.get('Content-Type'), 'Size:', len(r_db.content))

# 3. Test download Excel
r_xl = requests.get(baseUrl + data['download_url'])
assert r_xl.status_code == 200
print('Download Excel Status:', r_xl.status_code, 'Size:', len(r_xl.content))

# 4. Verify SQLite tables directly from disk
conn = sqlite3.connect('etl_warehouse.db')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
print('Tablas en etl_warehouse.db:', tables)
for t in tables:
    c.execute(f"SELECT COUNT(*) FROM {t}")
    print(f"  Tabla {t}: {c.fetchone()[0]} filas")
conn.close()

print('\nPRUEBA END-TO-END COMPLETADA CON ÉXITO!')


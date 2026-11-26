import io, sqlite3, hashlib, hmac, secrets, json
from contextlib import closing
from datetime import datetime
import numpy as np

class BaseDatos:
    def __init__(self, ruta):
        self.ruta = ruta
        with closing(sqlite3.connect(ruta)) as db, db:
            db.executescript('''CREATE TABLE IF NOT EXISTS usuarios(id INTEGER PRIMARY KEY,nombre TEXT UNIQUE,rol TEXT,sal TEXT,clave TEXT);
            CREATE TABLE IF NOT EXISTS ingresos(id INTEGER PRIMARY KEY,usuario INTEGER,fecha TEXT);
            CREATE TABLE IF NOT EXISTS archivos(id INTEGER PRIMARY KEY,usuario INTEGER,tipo TEXT,meta TEXT,datos BLOB);''')
            for nombre, rol in [('imagenes','imagenes'),('senales','senales')]:
                sal=secrets.token_hex(16)
                db.execute('INSERT OR IGNORE INTO usuarios(nombre,rol,sal,clave) VALUES(?,?,?,?)',(nombre,rol,sal,self.hashClave('Bio12345',sal)))
    def hashClave(self, clave, sal):
        return hashlib.pbkdf2_hmac('sha256',clave.encode(),bytes.fromhex(sal),200000).hex()
    def ingresar(self,nombre,clave):
        with closing(sqlite3.connect(self.ruta)) as db, db:
            fila=db.execute('SELECT * FROM usuarios WHERE nombre=?',(nombre,)).fetchone()
            if not fila or not hmac.compare_digest(fila[4],self.hashClave(clave,fila[3])): raise ValueError('Credenciales incorrectas')
            fecha=datetime.now().isoformat(sep=' ',timespec='seconds')
            db.execute('INSERT INTO ingresos(usuario,fecha) VALUES(?,?)',(fila[0],fecha))
            return fila[0],fila[1],fila[2],fecha
    def guardar(self,usuario,tipo,meta,matriz):
        b=io.BytesIO(); np.save(b,matriz,allow_pickle=False)
        with closing(sqlite3.connect(self.ruta)) as db, db:
            db.execute('INSERT INTO archivos(usuario,tipo,meta,datos) VALUES(?,?,?,?)',(usuario,tipo,json.dumps(meta),b.getvalue()))


   
    def guardarTabla(self, usuario, tabla):
        with closing(sqlite3.connect(self.ruta)) as db, db:
            db.execute('CREATE TABLE IF NOT EXISTS tablas(id INTEGER PRIMARY KEY, usuario INTEGER, datos TEXT)')
            return db.execute('INSERT INTO tablas(usuario,datos) VALUES(?,?)', (usuario, tabla.to_json(orient='table', force_ascii=False))).lastrowid

    def verTablas(self, usuario):
        with closing(sqlite3.connect(self.ruta)) as db, db:
            db.execute('CREATE TABLE IF NOT EXISTS tablas(id INTEGER PRIMARY KEY, usuario INTEGER, datos TEXT)')
            return [r[0] for r in db.execute('SELECT id FROM tablas WHERE usuario=?', (usuario,))]

    def recuperarTabla(self, usuario, identificador):
        import pandas as pd
        with closing(sqlite3.connect(self.ruta)) as db:
            fila = db.execute('SELECT datos FROM tablas WHERE usuario=? AND id=?', (usuario, identificador)).fetchone()
        if fila is None:
            raise ValueError('Tabla no disponible')
        return pd.read_json(io.StringIO(fila[0]), orient='table')

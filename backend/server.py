import json,sqlite3
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent; DB=BASE/"backend"/"app.db"; FRONT=BASE/"frontend"
PORT=5002

def conn(): c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def init():
 c=conn(); c.executescript((BASE/"backend"/"schema.sql").read_text())
 if c.execute("SELECT COUNT(*) FROM entries").fetchone()[0]==0: c.executemany("INSERT INTO entries(name,type,age_group,sex,sector,date,entry_time,exit_time) VALUES(?,?,?,?,?,?,?,?)",[("Ana Lima","aluno","adulto","F","Biblioteca","2026-09-18","08:10","12:05"),("Carlos Souza","servidor","adulto","M","Administração","2026-09-18","07:42","16:18"),("Marina Alves","visitante","adulto","F","Direção","2026-09-19","09:25","10:10"),("João Pedro","aluno","adolescente","M","Laboratório","2026-09-22","13:05","17:40")])
 c.commit();c.close()
def data(h): n=int(h.headers.get("Content-Length",0) or 0); return json.loads(h.rfile.read(n) or b"{}")
def send(h,x,status=200):
 b=json.dumps(x,ensure_ascii=False).encode();h.send_response(status);h.send_header("Content-Type","application/json; charset=utf-8");h.send_header("Content-Length",str(len(b)));h.end_headers();h.wfile.write(b)
class H(BaseHTTPRequestHandler):
 def log_message(self,*a): pass
 def do_GET(self):
  p=urlparse(self.path).path;c=conn()
  if p.startswith('/api/'):
   try: result=result={"total":c.execute("SELECT COUNT(*) FROM entries").fetchone()[0],"types":[dict(r) for r in c.execute("SELECT type name,COUNT(*) total FROM entries GROUP BY type ORDER BY total DESC")],"sectors":[dict(r) for r in c.execute("SELECT sector name,COUNT(*) total FROM entries GROUP BY sector ORDER BY total DESC")],"hours":[dict(r) for r in c.execute("SELECT substr(entry_time,1,2) hour,COUNT(*) total FROM entries GROUP BY hour ORDER BY total DESC")],"months":[dict(r) for r in c.execute("SELECT substr(date,1,7) month,COUNT(*) total FROM entries GROUP BY month ORDER BY month")]} if p=="/api/summary" else [dict(r) for r in c.execute("SELECT * FROM entries ORDER BY date DESC,entry_time DESC")]
   except Exception as e: result={'error':str(e)};send(self,result,500);c.close();return
   send(self,result);c.close();return
  f=FRONT/('index.html' if p=='/' else p.lstrip('/'))
  if f.exists(): b=f.read_bytes();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8' if f.suffix=='.html' else 'text/plain');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
  else: send(self,{'error':'Arquivo não encontrado'},404)
 def do_POST(self):
  p=urlparse(self.path).path;x=data(self);c=conn()
  try: result=cur=c.execute("INSERT INTO entries(name,type,age_group,sex,sector,date,entry_time,exit_time) VALUES(?,?,?,?,?,?,?,?)",(x["name"],x["type"],x["age_group"],x["sex"],x["sector"],x["date"],x["entry_time"],x.get("exit_time")));result=dict(c.execute("SELECT * FROM entries WHERE id=?",(cur.lastrowid,)).fetchone());c.commit();send(self,result,201)
  except Exception as e:c.rollback();send(self,{'error':str(e)},400)
  c.close()
 def do_PUT(self):
  p=urlparse(self.path).path; x=data(self); c=conn()
  try:
   i=int(p.rsplit('/',1)[1]); c.execute("UPDATE entries SET name=?,type=?,age_group=?,sex=?,sector=?,date=?,entry_time=?,exit_time=? WHERE id=?",(x['name'],x['type'],x['age_group'],x['sex'],x['sector'],x['date'],x['entry_time'],x.get('exit_time'),i)); c.commit(); send(self,dict(c.execute("SELECT * FROM entries WHERE id=?",(i,)).fetchone()))
  except Exception as e: c.rollback(); send(self,{'error':str(e)},400)
  c.close()
 def do_DELETE(self):
  p=urlparse(self.path).path; c=conn()
  try:
   i=int(p.rsplit('/',1)[1]); n=c.execute("DELETE FROM entries WHERE id=?",(i,)).rowcount; c.commit(); send(self,{'deleted':n==1})
  except Exception as e: c.rollback(); send(self,{'error':str(e)},400)
  c.close()
if __name__=='__main__': init(); print(f'http://127.0.0.1:{PORT}'); ThreadingHTTPServer(('127.0.0.1',PORT),H).serve_forever()

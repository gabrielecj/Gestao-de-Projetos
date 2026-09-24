import json,sqlite3
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent;DB=BASE/"backend/projects.db";FRONT=BASE/"frontend";PORT=5003
def conn():
 c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;return c
def init():
 c=conn();c.executescript((BASE/"backend/schema.sql").read_text())
 if c.execute("select count(*) from projects").fetchone()[0]==0:
  c.executemany("insert into projects(name,description,status,priority,due_date) values(?,?,?,?,?)",[("Portal Institucional","Atualização do site e conteúdo","Em andamento","Média","2026-10-05"),("App de Eventos","Fluxo de inscrição e agenda","A fazer","Alta","2026-10-12"),("Relatório Mensal","Consolidação de indicadores","Concluído","Baixa","2026-09-20")])
  c.executemany("insert into tasks(project_id,title,responsible,due_date,priority,status) values(?,?,?,?,?,?)",[(1,"Revisar arquitetura","Ana","2026-09-25","Alta","Em andamento"),(1,"Validar protótipo","Lucas","2026-09-27","Média","A fazer"),(2,"Definir escopo","Clara","2026-09-30","Alta","A fazer"),(3,"Publicar relatório","Ana","2026-09-20","Baixa","Concluído")])
 c.commit();c.close()
def body(h):
 n=int(h.headers.get("Content-Length",0) or 0);return json.loads(h.rfile.read(n) or b"{}")
def send(h,x,status=200):
 b=json.dumps(x,ensure_ascii=False).encode();h.send_response(status);h.send_header("Content-Type","application/json; charset=utf-8");h.send_header("Content-Length",str(len(b)));h.end_headers();h.wfile.write(b)
class H(BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  p=urlparse(self.path).path;c=conn()
  if p.startswith('/api/'):
   if p=='/api/summary':r={"projects":[dict(x) for x in c.execute("select status,count(*) total from projects group by status")],"tasks":[dict(x) for x in c.execute("select status,count(*) total from tasks group by status")]}
   elif p=='/api/projects':r=[dict(x) for x in c.execute("select * from projects order by id desc")]
   elif p=='/api/tasks':r=[dict(x) for x in c.execute("select t.*,p.name project_name from tasks t join projects p on p.id=t.project_id order by t.id desc")]
   else:r={"error":"Rota não encontrada"};send(self,r,404);c.close();return
   send(self,r);c.close();return
  f=FRONT/('index.html' if p=='/' else p.lstrip('/'))
  if f.exists():b=f.read_bytes();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
  else:send(self,{"error":"Arquivo não encontrado"},404)
 def do_POST(self):
  p=urlparse(self.path).path;x=body(self);c=conn()
  try:
   if p=='/api/projects':cur=c.execute("insert into projects(name,description,status,priority,due_date) values(?,?,?,?,?)",(x['name'],x.get('description',''),x.get('status','A fazer'),x.get('priority','Média'),x.get('due_date','')))
   elif p=='/api/tasks':cur=c.execute("insert into tasks(project_id,title,responsible,due_date,priority,status) values(?,?,?,?,?,?)",(x['project_id'],x['title'],x.get('responsible',''),x.get('due_date',''),x.get('priority','Média'),x.get('status','A fazer')))
   else:raise ValueError('Rota não encontrada')
   c.commit();table='projects' if p=='/api/projects' else 'tasks';r=dict(c.execute(f"select * from {table} where id=?",(cur.lastrowid,)).fetchone());send(self,r,201)
  except Exception as e:c.rollback();send(self,{"error":str(e)},400)
  c.close()
 def do_PUT(self):
  p=urlparse(self.path).path;x=body(self);c=conn()
  try:
   i=int(p.rsplit('/',1)[1])
   if p.startswith('/api/projects/'):c.execute("update projects set name=?,description=?,status=?,priority=?,due_date=? where id=?",(x['name'],x.get('description',''),x['status'],x['priority'],x.get('due_date',''),i));r=c.execute("select * from projects where id=?",(i,)).fetchone()
   else:c.execute("update tasks set project_id=?,title=?,responsible=?,due_date=?,priority=?,status=? where id=?",(x['project_id'],x['title'],x.get('responsible',''),x.get('due_date',''),x['priority'],x['status'],i));r=c.execute("select * from tasks where id=?",(i,)).fetchone()
   if not r:raise ValueError('Registro não encontrado')
   c.commit();send(self,dict(r))
  except Exception as e:c.rollback();send(self,{"error":str(e)},400)
  c.close()
 def do_DELETE(self):
  p=urlparse(self.path).path;c=conn()
  try:
   i=int(p.rsplit('/',1)[1]);n=c.execute("delete from projects where id=?",(i,)).rowcount if p.startswith('/api/projects/') else c.execute("delete from tasks where id=?",(i,)).rowcount;c.commit();send(self,{"deleted":n==1})
  except Exception as e:c.rollback();send(self,{"error":str(e)},400)
  c.close()
if __name__=='__main__':init();print(f'http://127.0.0.1:{PORT}');ThreadingHTTPServer(('127.0.0.1',PORT),H).serve_forever()

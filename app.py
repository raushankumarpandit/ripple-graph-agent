import os
import threading
from urllib.parse import urlparse
from flask import Flask, jsonify, request, send_from_directory
from dotenv import load_dotenv
from graph import Store
from agent import investigate

load_dotenv()

def create_app(store=None):
 app=Flask(__name__,static_folder='static')
 app.config['MAX_CONTENT_LENGTH']=16*1024
 db=store if store is not None else Store()
 lock=threading.RLock()
 @app.before_request
 def local_write_guard():
  if request.method=='POST':
   origin=request.headers.get('Origin')
   if origin and urlparse(origin).netloc!=request.host: return jsonify(error='Cross-origin writes are not allowed.'),403
   if not request.is_json: return jsonify(error='Use application/json.'),415
 @app.errorhandler(ValueError)
 def invalid(e): return jsonify(error=str(e)),400
 @app.errorhandler(Exception)
 def unexpected(e):
  from werkzeug.exceptions import HTTPException
  if isinstance(e,HTTPException): return jsonify(error=e.description),e.code
  app.logger.error('Request failed: %s',type(e).__name__)
  return jsonify(error='Could not complete the request. Check that FalkorDB is running and seeded; inspect your terminal. No successful result was fabricated.'),503
 @app.get('/')
 def index(): return send_from_directory('static','index.html')
 @app.get('/api/state')
 def state():
  with lock:
   return jsonify(topology=db.topology(),history=db.history(),tasks=db.tasks(),ai_available=bool(os.getenv('GEMINI_API_KEY')),model=os.getenv('GEMINI_MODEL','gemini-3.8-flash'))
 @app.post('/api/seed')
 def seed():
  with lock: db.seed()
  return jsonify(ok=True)
 @app.post('/api/investigate')
 def run():
  data=request.get_json()
  service=data.get('service',''); question=data.get('question','Investigate this outage and recommend a response.')
  if not isinstance(service,str) or not isinstance(question,str) or len(question)>2000: raise ValueError('Invalid request or question too long.')
  with lock: report=investigate(db,service,question,data.get('ai') is True)
  return jsonify(report)
 @app.get('/api/report/<iid>')
 def report(iid):
  with lock: return jsonify(db.report(iid))
 @app.post('/api/approve')
 def approve():
  with lock: return jsonify(db.approve(request.get_json().get('id','')))
 @app.post('/api/demo-edge')
 def edge():
  enabled=request.get_json().get('enabled')
  if type(enabled) is not bool: raise ValueError('enabled must be boolean.')
  with lock: db.change_demo_edge(enabled)
  return jsonify(ok=True)
 return app

if __name__=='__main__':
 create_app().run(host='127.0.0.1',port=int(os.getenv('PORT','5050')),debug=False)

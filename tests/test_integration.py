"""Real FalkorDB integration tests. RIPPLE_TEST_LITE=1 uses embedded FalkorDB."""
import os
import sys
import uuid
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from graph import Store
from agent import investigate
from app import create_app

@pytest.fixture(scope='module')
def db(tmp_path_factory):
 if os.getenv('RIPPLE_TEST_LITE')=='1':
  from redislite.falkordb_client import FalkorDB
  client=FalkorDB(str(tmp_path_factory.mktemp('db')/'test.rdb'))
 else:
  from falkordb import FalkorDB
  client=FalkorDB(host=os.getenv('FALKOR_HOST','127.0.0.1'),port=int(os.getenv('FALKOR_PORT','6379')))
 graph=client.select_graph('ripple_test_'+uuid.uuid4().hex)
 store=Store(graph); store.seed()
 yield store
 graph.delete()

@pytest.mark.parametrize('service,expected',[
 ('ledger',{'payments','checkout','orders','storefront','refunds','analytics'}),
 ('payments',{'checkout','orders','storefront','refunds','analytics'}),
 ('identity',{'login'}),('catalog',{'search'}),('search',set()),('notifications',set())])
def test_impact_sets(db,service,expected):
 assert {s['id'] for s in db.impact(service)['affected']}==expected

def test_exact_evidence_path(db):
 s=next(s for s in db.impact('ledger')['affected'] if s['id']=='storefront')
 assert ['Storefront','Checkout','Payments','Ledger DB'] in s['paths']
 assert s['hops']==3

def test_missing_owner_and_runbook(db):
 context=db.context('analytics')
 assert context['owner'].startswith('Unknown')
 assert context['runbooks']==[]

def test_graph_change_changes_answer(db):
 db.change_demo_edge(True)
 assert 'notifications' in {s['id'] for s in db.impact('ledger')['affected']}
 db.change_demo_edge(False)
 assert 'notifications' not in {s['id'] for s in db.impact('ledger')['affected']}

def test_memory_and_idempotent_approval(db):
 first=investigate(db,'ledger','First check')
 # New application Store object reads persisted graph state.
 reopened=Store(db.graph)
 second=investigate(reopened,'ledger','What did we learn?')
 assert first['id'] in {m['id'] for m in second['memory']}
 assert len(reopened.tasks())==0
 one=reopened.approve(second['id']);two=reopened.approve(second['id'])
 assert one['id']==two['id']
 assert len(reopened.tasks())==1
 assert reopened.report(first['id'])['summary']==first['summary']

def test_seed_idempotent(db):
 before=db.topology();db.seed();assert db.topology()==before

def test_saved_map_is_stable_after_graph_change(db):
 before=investigate(db,'ledger','Snapshot before dependency change')
 try:
  db.change_demo_edge(True)
  after=investigate(db,'ledger','Snapshot after dependency change')
  edge={'source':'notifications','target':'payments'}
  assert edge not in db.report(before['id'])['topology']['edges']
  assert edge in after['topology']['edges']
 finally:
  db.change_demo_edge(False)

def test_api_validation_and_read_write_flow(db):
 client=create_app(db).test_client()
 assert client.get('/').status_code==200
 assert client.get('/api/state').json['topology']['nodes']
 assert client.post('/api/investigate',json={'service':"x') DELETE n"}).status_code==400
 assert client.post('/api/demo-edge',json={'enabled':'false'}).status_code==400
 assert client.post('/api/demo-edge',json={'enabled':False},headers={'Origin':'https://evil.example'}).status_code==403
 r=client.post('/api/investigate',json={'service':'identity','ai':False})
 assert r.status_code==200
 assert len(r.json['impact']['affected'])==1
 assert client.get('/api/report/'+r.json['id']).status_code==200
 assert client.post('/api/approve',json={'id':r.json['id']}).status_code==200

def test_ai_requires_key(db,monkeypatch):
 monkeypatch.delenv('GEMINI_API_KEY',raising=False)
 with pytest.raises(ValueError,match='GEMINI_API_KEY'): investigate(db,'ledger','test',True)

def test_ai_tool_protocol(db,monkeypatch):
 # Contract test, NOT a live model evaluation.
 monkeypatch.setenv('GEMINI_API_KEY','test-key')
 replies=[{'candidates':[{'content':{'role':'model','parts':[{'functionCall':{'name':n,'args':{}}} for n in ['get_impact','get_context','get_memory']]}}]}, {'candidates':[{'content':{'role':'model','parts':[{'text':'Ledger DB has downstream dependency impact. Review the evidence.'}]}}]}]
 class Reply:
  ok=True
  def __init__(self,payload): self.payload=payload
  def json(self):return self.payload
 def post(*args,**kwargs):return Reply(replies.pop(0))
 monkeypatch.setattr('agent.requests.post',post)
 r=investigate(db,'ledger','Investigate',True)
 assert len(r['trace'])==3
 assert r['mode']=='Gemini tool-calling agent'

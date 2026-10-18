"""All product data and memory live in FalkorDB. No in-memory graph fallback."""
import json
import os
import uuid
from datetime import datetime, timezone
from falkordb import FalkorDB

QUERIES = {
 'impact': '''MATCH p=(s:Service)-[:DEPENDS_ON*1..8]->(root:Service {id:$service})
 RETURN s.id, s.name, s.criticality, [n IN nodes(p) | n.name], length(p)
 ORDER BY length(p), s.id''',
 'context': '''MATCH (s:Service {id:$service})
 OPTIONAL MATCH (s)-[:OWNED_BY]->(t:Team)
 OPTIONAL MATCH (s)-[:HAS_RUNBOOK]->(r:Runbook)
 RETURN s.name, t.name, r.title, r.steps, r.source''',
 'incidents': '''MATCH (i:Incident)-[:INVOLVED]->(s:Service {id:$service})
 RETURN i.id, i.summary, i.resolution, i.source ORDER BY i.id''',
 'memory': '''MATCH (i:Investigation)-[:ABOUT]->(s:Service {id:$service})
 RETURN i.id, i.created, i.summary ORDER BY i.created DESC LIMIT 5''',
}

class Store:
 def __init__(self, graph=None):
  self.client = None
  if graph is None:
   self.client=FalkorDB(host=os.getenv('FALKOR_HOST','127.0.0.1'), port=int(os.getenv('FALKOR_PORT','6379')), password=os.getenv('FALKOR_PASSWORD') or None, socket_timeout=10)
   graph=self.client.select_graph(os.getenv('FALKOR_GRAPH','ripple'))
  self.graph=graph
 def q(self, query, params=None):
  return self.graph.query(query, params or {}).result_set
 def seed(self):
  services=[('ledger','Ledger DB', 'critical',0),('payments','Payments','critical',1),('checkout','Checkout','critical',2),('orders','Orders','high',2),('storefront','Storefront','high',3),('refunds','Refunds','high',2),('analytics','Analytics','medium',3),('notifications','Notifications','medium',2),('identity','Identity','critical',0),('login','Login','high',1),('search','Search','medium',1),('catalog','Catalog','medium',0)]
  for sid,name,criticality,layer in services:
   self.q('MERGE (s:Service {id:$id}) ON CREATE SET s.name=$name,s.criticality=$criticality,s.layer=$layer',dict(id=sid,name=name,criticality=criticality,layer=layer))
  for a,b in [('payments','ledger'),('checkout','payments'),('orders','payments'),('storefront','checkout'),('refunds','payments'),('analytics','orders'),('login','identity'),('search','catalog')]:
   self.q('MATCH (a:Service {id:$a}),(b:Service {id:$b}) MERGE (a)-[:DEPENDS_ON]->(b)',dict(a=a,b=b))
  for sid,team in [('ledger','Data Platform'),('payments','Payments Team'),('checkout','Commerce Team'),('orders','Commerce Team'),('storefront','Commerce Team'),('refunds','Payments Team'),('identity','Identity Team'),('login','Identity Team'),('catalog','Discovery Team'),('search','Discovery Team'),('notifications','Messaging Team')]:
   self.q('MATCH (s:Service {id:$id}) MERGE (t:Team {name:$team}) MERGE (s)-[:OWNED_BY]->(t)',dict(id=sid,team=team))
  runbooks=[('ledger','RB-001','Ledger connection exhaustion','Inspect connection pool and database health; compare active connections to limits; ask Data Platform to review recent changes before any restart.'),('identity','RB-002','Identity availability','Inspect authentication errors and identity provider health; ask Identity Team to validate recovery before restoring traffic.'),('payments','RB-003','Payments degradation','Check Ledger DB health first; pause retries if they amplify load; ask Payments Team to review payment reconciliation.')]
  for sid,rid,title,steps in runbooks:
   self.q('MATCH (s:Service {id:$id}) MERGE (r:Runbook {id:$rid}) SET r.title=$title,r.steps=$steps,r.source=$source MERGE (s)-[:HAS_RUNBOOK]->(r)',dict(id=sid,rid=rid,title=title,steps=steps,source='synthetic://runbooks/'+rid))
  for iid,sid,summary,resolution in [('INC-001','ledger','Connection pool exhaustion delayed payments','Data Platform reduced excessive client connections after verifying database health.'),('INC-002','payments','Retry storm increased payment latency','Payments Team throttled retry traffic and reconciled delayed requests.'),('INC-003','identity','Identity provider timeout prevented logins','Identity Team restored the provider connection and verified login flows.')]:
   self.q('MATCH (s:Service {id:$sid}) MERGE (i:Incident {id:$id}) SET i.summary=$summary,i.resolution=$resolution,i.source=$source MERGE (i)-[:INVOLVED]->(s)',dict(sid=sid,id=iid,summary=summary,resolution=resolution,source='synthetic://incidents/'+iid))
 def topology(self):
  nodes=[dict(id=r[0],name=r[1],criticality=r[2],layer=r[3]) for r in self.q('MATCH (s:Service) RETURN s.id,s.name,s.criticality,s.layer ORDER BY s.id')]
  edges=[dict(source=r[0],target=r[1]) for r in self.q('MATCH (a:Service)-[:DEPENDS_ON]->(b:Service) RETURN a.id,b.id')]
  return dict(nodes=nodes,edges=edges)
 def tools(self,service):
  if not self.q('MATCH (s:Service {id:$id}) RETURN s.id',{'id':service}): raise ValueError('Unknown service. Choose one from the list.')
  return {
   'get_impact':lambda:self.impact(service),
   'get_context':lambda:self.context(service),
   'get_memory':lambda:self.memory(service),
  }
 def impact(self,service):
  rows=self.q(QUERIES['impact'],{'service':service})
  affected={}
  for sid,name,criticality,path,hops in rows:
   if sid==service: continue
   if sid not in affected: affected[sid]=dict(id=sid,name=name,criticality=criticality,paths=[],hops=hops)
   affected[sid]['paths'].append(path)
  for s in affected.values():
   owner=self.q('MATCH (s:Service {id:$id}) OPTIONAL MATCH (s)-[:OWNED_BY]->(t:Team) RETURN t.name',{'id':s['id']})
   s['owner']=owner[0][0] or 'Unknown — assign an owner'
  return {'affected':list(affected.values()),'scope':'Potential dependency impact, not proof of observed failure. Traversal bounded to 8 hops.', 'cypher':QUERIES['impact']}
 def context(self,service):
  rows=self.q(QUERIES['context'],{'service':service})
  return dict(service=service,name=rows[0][0],owner=rows[0][1] or 'Unknown — assign an owner',runbooks=[dict(title=r[2],steps=r[3],source=r[4]) for r in rows if r[2]],incidents=[dict(id=r[0],summary=r[1],resolution=r[2],source=r[3]) for r in self.q(QUERIES['incidents'],{'service':service})])
 def memory(self,service):
  return [dict(id=r[0],created=r[1],summary=r[2]) for r in self.q(QUERIES['memory'],{'service':service})]
 def save(self,report):
  report['id']=str(uuid.uuid4())
  report['created']=datetime.now(timezone.utc).isoformat()
  self.q('MATCH (s:Service {id:$service}) CREATE (i:Investigation {id:$id,created:$created,summary:$summary,payload:$payload}) CREATE (i)-[:ABOUT]->(s)',dict(service=report['service'],id=report['id'],created=report['created'],summary=report['summary'],payload=json.dumps(report)))
  return report
 def report(self,iid):
  rows=self.q('MATCH (i:Investigation {id:$id}) RETURN i.payload',{'id':iid})
  if not rows: raise ValueError('Investigation not found.')
  return json.loads(rows[0][0])
 def history(self):
  return [dict(id=r[0],created=r[1],summary=r[2],service=r[3]) for r in self.q('MATCH (i:Investigation)-[:ABOUT]->(s:Service) RETURN i.id,i.created,i.summary,s.name ORDER BY i.created DESC LIMIT 20')]
 def approve(self,iid):
  report=self.report(iid)
  taskid='TASK-'+iid[:8]
  self.q('MATCH (i:Investigation {id:$id}) MERGE (t:Task {id:$task}) ON CREATE SET t.status="approved",t.title=$title,t.owner=$owner,t.created=$created MERGE (i)-[:PROPOSED]->(t)',dict(id=iid,task=taskid,title=report['action']['title'],owner=report['action']['owner'],created=datetime.now(timezone.utc).isoformat()))
  return dict(id=taskid,title=report['action']['title'],owner=report['action']['owner'],status='approved',scope='Local response task only; no production action or message sent.')
 def tasks(self):
  return [dict(id=r[0],title=r[1],owner=r[2],status=r[3]) for r in self.q('MATCH (t:Task) RETURN t.id,t.title,t.owner,t.status ORDER BY t.created DESC')]
 def change_demo_edge(self,enabled):
  if enabled:
   self.q('MATCH (a:Service {id:"notifications"}),(b:Service {id:"payments"}) MERGE (a)-[:DEPENDS_ON]->(b)')
  else:
   self.q('MATCH (:Service {id:"notifications"})-[r:DEPENDS_ON]->(:Service {id:"payments"}) DELETE r')

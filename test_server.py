import unittest
import io
import urllib.error
import urllib.request
import json,time
import threading
from unittest.mock import patch
import server
class MarketTests(unittest.TestCase):
 def test_ema_seed_and_recurrence(self):
  self.assertEqual(server.ema([1,2],3),[])
  self.assertEqual(server.ema([1,2,3,4],3),[None,None,2,3])
 def test_closed_candles_and_oi_window(self):
  clock=2_000_000_000_000
  candles=[[clock-(400-i)*14400000,0,0,0,str(10+i/100),0,clock-(399-i)*14400000-1] for i in range(400)]
  candles.append([clock,0,0,0,'999999',0,clock+14400000])
  def api(path,params):
   if 'ticker' in path:return {'lastPrice':'14','priceChangePercent':'2','quoteVolume':'100','closeTime':clock}
   if 'klines' in path:return candles
   return [{'timestamp':clock-3600000,'sumOpenInterest':'100'},{'timestamp':clock,'sumOpenInterest':'110'}]
  with patch('server.api',side_effect=api),patch('server.now',return_value=clock):_,m=server.market(server.PROJECTS[0])
  self.assertEqual(m['klineCount'],400)
  self.assertLess(m['ema200'],14)
  self.assertAlmostEqual(m['oiChange1h'],10)
  self.assertEqual(m['close4h'],13.99)
 def test_short_oi_window_is_not_one_hour(self):
  clock=2_000_000_000_000
  def api(path,params):
   if 'ticker' in path:raise TimeoutError()
   if 'klines' in path:return []
   return [{'timestamp':clock-300000,'sumOpenInterest':'100'},{'timestamp':clock,'sumOpenInterest':'110'}]
  with patch('server.api',side_effect=api):_,m=server.market(server.PROJECTS[0])
  self.assertNotIn('oiChange1h',m)
  self.assertIn('oiWindow',m['errors'])
  self.assertNotIn('price',m)
 def test_missing_token_is_explicit(self):
  with patch('server.TOKEN',''):events,status=server.provider_news(server.PROJECTS[0])
  self.assertEqual(events,[])
  self.assertEqual(status['OpenTwitter']['status'],'missing_credential')
 def test_public_source_success_status(self):
  row={'id':'real','p':'near','title':'Official title'}
  with patch('server.TOKEN',''),patch('server.public_news',return_value=[row]):
   pid,items,status=server.refresh_news(server.PROJECTS[1])
  self.assertEqual(pid,'near')
  self.assertEqual(items,[row])
  self.assertEqual(status['官网资讯']['status'],'ok')
  self.assertEqual(status['官网资讯']['count'],1)
class ProviderNewsFilterTests(unittest.TestCase):
 def provider(self,coin_rows,keyword_rows):
  def fake(url,payload=None):
   if url.endswith('/news_search'):
    return json.dumps({'success':True,'data':coin_rows if 'coins' in payload else keyword_rows})
   return json.dumps({'success':True,'data':[]})
  return fake
 def test_conflicting_provider_mapping_is_rejected_by_coin_query(self):
  row={'link':'https://example.com/near-upgrade','text':'NEAR Protocol announces a new upgrade','ts':1700000000000,'newsType':'OpenNews','coins':[{'symbol':'BTC'}]}
  with patch('server.TOKEN','test-token'),patch('server.request',side_effect=self.provider([row],[dict(row)])):
   events,status=server.provider_news(server.PROJECTS[1])
  coin=[e for e in events if e['matchReason'].startswith('币种检索')]
  keyword=[e for e in events if e['matchReason'].startswith('关键词补充检索')]
  self.assertEqual(len(coin),0)
  self.assertEqual(len(keyword),1)
  self.assertTrue(keyword[0].get('providerMismatch'))
  self.assertIn('其他币种',keyword[0]['matchReason'])
  self.assertEqual(status['OpenNews']['count'],0)
  self.assertEqual(status['OpenNews关键词']['count'],1)
 def test_matching_or_absent_mapping_is_accepted(self):
  row={'link':'https://example.com/near-upgrade','text':'NEAR Protocol announces a new upgrade','ts':1700000000000,'newsType':'OpenNews','coins':[{'symbol':'NEAR'}]}
  absent=dict(row);absent.pop('coins');absent['link']='https://example.com/near-upgrade-2'
  with patch('server.TOKEN','test-token'),patch('server.request',side_effect=self.provider([row],[absent])):
   events,status=server.provider_news(server.PROJECTS[1])
  self.assertEqual(status['OpenNews']['count'],1)
  self.assertEqual(status['OpenNews关键词']['count'],1)
  self.assertTrue(all('providerMismatch' not in e for e in events))
  coin=next(e for e in events if e['matchReason'].startswith('币种检索'))
  self.assertIn('包含 NEAR',coin['matchReason'])
 def test_mismatch_records_never_become_high_candidates(self):
  from news_quality import annotate
  base={'id':'x','p':'near','type':'news','title':'NEAR Protocol exploit drains funds','summary':'NEAR Protocol exploit drains funds','publishedAt':int(time.time()*1000)}
  self.assertTrue(annotate(base,int(time.time()*1000))['high'])
  out=annotate({**base,'providerMismatch':True},int(time.time()*1000))
  self.assertFalse(out['high'])
  self.assertIn('不一致',out['priorityReason'])

class ChartConcurrencyTests(unittest.TestCase):
 def setUp(self):
  server.CHART_CACHE.clear();server.CHART_ERRORS.clear();server.CHART_INFLIGHT.clear()
  self.rows=[[i*3600000,'2','3','1','2','10',i*3600000+3599999] for i in range(2)]
  self.snapshot=lambda rows,period,at,ema:{'period':period,'fetchedAt':at,'candles':rows}
 def tearDown(self):
  server.CHART_CACHE.clear();server.CHART_ERRORS.clear();server.CHART_INFLIGHT.clear()
 def test_different_projects_fetch_in_parallel(self):
  calls=[]
  def fake_api(path,params):calls.append(params['symbol']);time.sleep(0.3);return self.rows
  out={}
  with patch('server.api',side_effect=fake_api),patch('server.charts.snapshot',side_effect=self.snapshot):
   threads=[threading.Thread(target=lambda pid: out.__setitem__(pid,server.chart_data(pid,'1h')),args=(pid,)) for pid in ['near','pha']]
   start=time.perf_counter()
   for t in threads:t.start()
   for t in threads:t.join()
   elapsed=time.perf_counter()-start
  self.assertLess(elapsed,0.55)
  self.assertEqual(len(calls),2)
  self.assertEqual(set(out),{'near','pha'})
 def test_same_key_single_flight(self):
  calls=[]
  def fake_api(path,params):calls.append(1);time.sleep(0.2);return self.rows
  out=[]
  with patch('server.api',side_effect=fake_api),patch('server.charts.snapshot',side_effect=self.snapshot):
   threads=[threading.Thread(target=lambda: out.append(server.chart_data('near','1h'))) for _ in range(3)]
   for t in threads:t.start()
   for t in threads:t.join()
  self.assertEqual(len(calls),1)
  self.assertEqual(len(out),3)
  self.assertTrue(all(o is out[0] for o in out))
 def test_cache_ttl_reuses_recent_result(self):
  calls=[]
  def fake_api(path,params):calls.append(1);return self.rows
  with patch('server.api',side_effect=fake_api),patch('server.charts.snapshot',side_effect=self.snapshot):
   first=server.chart_data('near','1h');second=server.chart_data('near','1h')
  self.assertEqual(len(calls),1)
  self.assertIs(first,second)

class ClusterCacheTests(unittest.TestCase):
 def setUp(self):
  self.events=server.DATA['events'];self.sources=server.DATA['sources'];self.rev=server.EVENTS_REV
  server.DATA['events']=[];server.DATA['sources']={};server.EVENTS_REV+=1
  server.CLUSTER_CACHE.update(key=None,value=None)
 def tearDown(self):
  server.DATA['events']=self.events;server.DATA['sources']=self.sources;server.EVENTS_REV=self.rev
  server.CLUSTER_CACHE.update(key=None,value=None)
 def test_reuses_result_until_inputs_change(self):
  calls=[]
  real=server.cluster
  def counting(rows,stats=None):calls.append(len(rows));return real(rows,stats)
  with patch('server.cluster',side_effect=counting):
   a=server.clustered_news();b=server.clustered_news()
   self.assertIs(a,b)
   self.assertEqual(len(calls),1)
   server.EVENTS_REV+=1
   c=server.clustered_news()
   self.assertIsNot(a,c)
   self.assertEqual(len(calls),2)
 def test_store_news_bumps_revision(self):
  before=server.EVENTS_REV
  item={'id':'t1','p':'near','type':'news','title':'t','summary':'s','url':'https://e.example/1','publishedAt':1}
  server.store_news('near',[item],{'test':{'status':'ok'}})
  self.assertEqual(server.EVENTS_REV,before+1)

class RedirectSecurityTests(unittest.TestCase):
 def make_request(self):
  return urllib.request.Request('https://ai.6551.io/open/news_search',data=b'{}',headers={'Authorization':'Bearer audit-placeholder'})
 def test_cross_host_redirect_is_blocked_for_auth_requests(self):
  handler=server.CrossHostRedirectBlocked()
  for code in [301,302,303]:
   with self.assertRaises(urllib.error.HTTPError) as ctx:
    handler.redirect_request(self.make_request(),None,code,'redirect',{},'https://redirect.example/collect')
   self.assertEqual(ctx.exception.code,code)
   ctx.exception.close()
 def test_same_host_redirect_keeps_authorization(self):
  handler=server.CrossHostRedirectBlocked()
  new=handler.redirect_request(self.make_request(),None,302,'redirect',{},'https://ai.6551.io/open/other')
  self.assertEqual(new.get_header('Authorization'),'Bearer audit-placeholder')
 def test_scheme_or_port_change_is_blocked_for_auth_requests(self):
  handler=server.CrossHostRedirectBlocked()
  for url in ['http://ai.6551.io/open/news_search','https://ai.6551.io:444/open/news_search']:
   with self.assertRaises(urllib.error.HTTPError) as ctx:
    handler.redirect_request(self.make_request(),None,302,'redirect',{},url)
   self.assertEqual(ctx.exception.code,302)
   ctx.exception.close()
 def test_post_redirects_307_308_stay_rejected(self):
  handler=server.CrossHostRedirectBlocked()
  for code in [307,308]:
   fp=io.BytesIO()
   with self.assertRaises(urllib.error.HTTPError) as ctx:
    handler.redirect_request(self.make_request(),fp,code,'redirect',{},'https://ai.6551.io/open/other')
   ctx.exception.close()
 def test_only_auth_opener_blocks_cross_host(self):
  def kinds(opener):return {type(h) for h in opener.handlers}
  self.assertNotIn(server.CrossHostRedirectBlocked,kinds(server._OPENERS['plain']))
  self.assertIn(server.CrossHostRedirectBlocked,kinds(server._OPENERS['auth']))
 def test_auth_request_uses_blocking_opener_and_bearer_header(self):
  seen=[]
  class FakeOpener:
   def open(self,req,timeout=None):
    seen.append((req.full_url,req.get_header('Authorization')))
    class R:
     def read(self,n):return b'{}'
     def __enter__(self):return self
     def __exit__(self,*args):return False
    return R()
  with patch.dict(server._OPENERS,{'auth':FakeOpener()}),patch('server.TOKEN','audit-placeholder'):
   self.assertEqual(server.request('https://ai.6551.io/open/news_search',{}),'{}')
  self.assertEqual(seen,[('https://ai.6551.io/open/news_search','Bearer audit-placeholder')])

if __name__=='__main__':unittest.main()

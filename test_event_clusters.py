import unittest
import random
from event_clusters import cluster,progress_candidates,same_event
class ClusterTests(unittest.TestCase):
 def event(self,id,body,p='near',date=1000):return dict(id=id,p=p,publishedAt=date,summary=body,url='https://x.com/a/status/'+id,sourcesList=[{'name':'Source '+id,'url':'https://x.com/a/status/'+id}])
 def test_progress_only_marks_new_structured_claims(self):
  first=self.event('1','Raised $100 million https://near.org/blog/funding')
  repeat=self.event('2','Raised $100 million https://near.org/blog/funding',date=2000)
  update=self.event('3','Now live, funding reaches $200 million https://near.org/blog/funding',date=3000)
  self.assertEqual(progress_candidates([first,repeat]),[])
  candidates=progress_candidates([first,repeat,update]);self.assertEqual(len(candidates),1)
  self.assertIn('上线确认',candidates[0]['signals'])
 def test_common_original_merges_with_provenance(self):
  r=cluster([self.event('1','Launch https://near.org/blog/upgrade-2026'),self.event('2','Team explains https://near.org/blog/upgrade-2026',date=2000)])
  self.assertEqual(len(r),1);self.assertEqual(len(r[0]['relatedItems']),2);self.assertEqual(r[0]['sourceCount'],2)
 def test_different_project_date_and_homepage_do_not_merge(self):
  for second in [self.event('2','https://near.org/'),self.event('2','https://near.org/blog/upgrade-2026',p='pha'),self.event('2','https://near.org/blog/upgrade-2026',date=200000000)]:
   self.assertEqual(len(cluster([self.event('1','https://near.org/blog/upgrade-2026'),second])),2)
 def test_changed_numeric_claims_not_merged_by_text(self):
  text='NEAR Protocol '+('this upgrade improves infrastructure and performance for every developer building decentralized applications across the network '*4)
  self.assertEqual(len(cluster([self.event('1',text+' 100 million'),self.event('2',text+' 200 million')])),2)
 def test_short_generic_headlines_are_not_merged(self):
  self.assertEqual(len(cluster([self.event('1','NEAR launches upgrade'),self.event('2','NEAR launches upgrade')])),2)
class ClusterIndexTests(unittest.TestCase):
 def tok(self,n):
  s=''
  while True:
   s=chr(97+n%26)+s;n=n//26
   if n==0:return s
 def test_dense_unique_events_do_no_pairwise_comparisons(self):
  rows=[dict(id='d%04d'%i,p='near',publishedAt=1000+i,summary=' '.join(self.tok(i*100+j) for j in range(40)),url='https://news.example/%04d'%i) for i in range(1600)]
  stats={}
  result=cluster(rows,stats=stats)
  self.assertEqual(len(result),1600)
  self.assertEqual(stats['match_checks'],0)
 def test_common_word_corpus_keeps_comparisons_bounded(self):
  common=' '.join('topic%d'%k for k in range(10))
  rows=[dict(id='c%04d'%i,p='pha',publishedAt=1000+i,summary=common+' '+' '.join(self.tok(10**6+i*100+j) for j in range(30)),url='https://news.example/c%04d'%i) for i in range(1600)]
  stats={}
  result=cluster(rows,stats=stats)
  self.assertEqual(len(result),1600)
  self.assertLess(stats['match_checks'],5000)
 def test_dense_posting_keeps_a_true_digit_match(self):
  def event(id,summary,date):return dict(id=id,p='near',publishedAt=date,summary=summary,url='https://news.example/'+id)
  body=' '.join('term%d'%i for i in range(40));rows=[event('other%d'%i,body+' '+str(1000+i),1000000+i*60000) for i in range(49)]
  rows.extend([event('anchor',body+' 42',4000000),event('match',body+' 42',4060000)])
  stats={};result=cluster(rows,stats=stats);anchor=next(item for item in result if item['id']=='anchor')
  self.assertEqual({item['id'] for item in anchor['relatedItems']},{'anchor','match'})
  self.assertLess(stats['match_checks'],5)
 def test_stopword_overlap_remains_a_complete_candidate(self):
  def event(id,summary,date):return dict(id=id,p='near',publishedAt=date,summary=summary,url='https://news.example/'+id)
  shared='the a an and or of to in on for with is are was were be been has have had will would it its this that these those as at by from not no new'
  first=event('stop-a',shared+' alpha',1000);second=event('stop-b',shared+' beta',2000)
  self.assertIsNotNone(same_event(first,second))
  self.assertEqual(len(cluster([first,second])),1)
 def test_project_partition_skips_cross_project_lookalikes(self):
  rows=[]
  for i in range(800):
   body=' '.join(self.tok(i*100+j) for j in range(40))
   rows.extend([dict(id='a%04d'%i,p='near',publishedAt=1000000+i,summary=body,url='https://news.example/a%04d'%i),dict(id='b%04d'%i,p='pha',publishedAt=1000000+i,summary=body,url='https://news.example/b%04d'%i)])
  stats={};result=cluster(rows,stats=stats)
  self.assertEqual(len(result),1600)
  self.assertEqual(stats['match_checks'],0)
 def build_mixed(self,rng):
  rows=[];t0=10**7
  for k in range(12):
   body=' '.join('pair%02d_%03d'%(k,j) for j in range(40))
   rows.append(dict(id='sim%02da'%k,p='near',publishedAt=t0+k*3600000,summary=body,url='https://news.example/sim-a-%d'%k))
   rows.append(dict(id='sim%02db'%k,p='near',publishedAt=t0+k*3600000+60000,summary=body,url='https://news.example/sim-b-%d'%k))
  for k in range(8):
   url='https://news.example/reference-%d'%k
   rows.append(dict(id='chg%02da'%k,p='pha',publishedAt=t0+1000+k*7000,summary=' '.join('r%02d_%03d'%(k,j) for j in range(12)),url=url))
   rows.append(dict(id='chg%02db'%k,p='pha',publishedAt=t0+2000+k*7000,summary=' '.join('s%02d_%03d'%(k,j) for j in range(15)),url=url))
  for k in range(10):
   body=' '.join('num%02d_%03d'%(k,j) for j in range(40))
   rows.append(dict(id='amt%02da'%k,p='nil',publishedAt=t0+2000+k*9000,summary=body+' 100',url='https://news.example/amt-a-%d'%k))
   rows.append(dict(id='amt%02db'%k,p='nil',publishedAt=t0+3000+k*9000,summary=body+' 200',url='https://news.example/amt-b-%d'%k))
  for i in range(40):
   rows.append(dict(id='noise%03d'%i,p='pha' if i%2 else 'near',publishedAt=t0+rng.randrange(0,60000000),summary=' '.join('z%03d_%03d'%(i,j) for j in range(rng.randrange(5,25))),url='https://news.example/z-%d'%i))
  dup=' '.join('n1_%02d'%j for j in range(40))
  rows.append(dict(id='notime1',p='near',summary=dup))
  rows.append(dict(id='notime2',p='near',summary=dup))
  rng.shuffle(rows)
  return rows
 def naive_groups(self,rows):
  groups=[]
  for e in sorted(rows,key=lambda x:(x.get('publishedAt') or 0,x['id'])):
   target=None;reason=None
   for group in reversed(groups):
    reason=same_event(group[0],e)
    if reason:target=group;break
   if target is None:groups.append([e])
   else:target.append({**e,'clusterReason':reason})
  return groups
 def test_indexed_grouping_matches_naive_algorithm(self):
  def shape_groups(groups):return sorted(tuple(sorted(e['id'] for e in g)) for g in groups)
  def shape_result(result):return sorted(tuple(sorted(x['id'] for x in (r.get('relatedItems') or [r]))) for r in result)
  for seed in [3,11,29]:
   rng=random.Random(seed)
   rows=self.build_mixed(rng)
   self.assertEqual(shape_result(cluster(rows)),shape_groups(self.naive_groups(rows)))

if __name__=='__main__':unittest.main()

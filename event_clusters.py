"""Conservative same-event grouping with inspectable reasons and full source retention."""
import re,hashlib,math
from collections import deque
from news_quality import canonical_url
from urllib.parse import urlsplit

WINDOW_MS=48*3600000
JACCARD_THRESHOLD=.92
def _words(e):return re.findall(r'[a-z0-9]+|[\u4e00-\u9fff]',re.sub(r'https?://\S+','',e.get('summary','')).lower())
def _digits(e):return set(re.findall(r'\d+(?:\.\d+)?',e.get('summary','')))

def references(e):
 urls=re.findall(r'https?://[^\s<>]+',e.get('summary',''))+[e.get('url','')]
 result=set()
 for url in urls:
  url=url.rstrip('.,，。)');u=urlsplit(url)
  if u.hostname in ['t.co','bit.ly'] or not u.hostname:continue
  if len(u.path.strip('/'))<8:continue
  if u.hostname in ['x.com','twitter.com'] and '/status/' not in u.path:continue
  result.add(canonical_url(url))
 return result

def _facts(e):return {'refs':references(e),'words':_words(e),'digits':_digits(e)}

def _match(af,bf,a,b):
 if a['p']!=b['p']:return None
 if not a.get('publishedAt') or not b.get('publishedAt') or abs(a['publishedAt']-b['publishedAt'])>WINDOW_MS:return None
 if af['refs']&bf['refs']:return '共同引用同一篇原文，发布时间相差不超过 48 小时'
 wa,wb=af['words'],bf['words']
 if min(len(wa),len(wb))<30:return None
 # Changed amounts/dates can be a new development and must remain separately visible.
 if af['digits']!=bf['digits']:return None
 sa,sb=set(wa),set(wb)
 if len(sa&sb)/max(1,len(sa|sb))>=JACCARD_THRESHOLD:return '正文高度重合，数字一致，发布时间相差不超过 48 小时'
 return None

def _prefix_words(words,frequency):
 # A fixed global ordering makes the Jaccard prefix filter complete rather than heuristic.
 ordered=sorted(set(words),key=lambda w:(frequency[w],w))
 length=len(ordered)-math.ceil(JACCARD_THRESHOLD*len(ordered))+1
 return tuple(ordered[:max(0,length)])

def same_event(a,b):return _match(_facts(a),_facts(b),a,b)

def progress_candidates(group):
 def facts(item):
  text=re.sub(r'https?://\S+','',item.get('summary','')).lower()
  values=set(re.findall(r'(?:\$\s*\d[\d,.]*|\d[\d,.]*\s*(?:%|million|billion|usd|usdt|万美元|亿美元|万枚|亿枚))',text))
  states={'上线确认':r'now live|is live|已上线|正式上线','暂停':r'has paused|suspended|暂停提现|暂停提款|已暂停','恢复':r'resumed|restored|已恢复|恢复提现','修复':r'has been patched|fix deployed|已修复|修复完成'}
  for label,pattern in states.items():
   if re.search(pattern,text):values.add(label)
  return values
 if len(group)<2:return []
 known=facts(group[0]);out=[]
 for item in group[1:]:
  if item.get('providerMismatch'):continue
  current=facts(item);added=current-known;known|=current
  if added and (item.get('publishedAt') or 0)>(group[0].get('publishedAt') or 0):
   key=hashlib.sha256('|'.join(sorted(added)).encode()).hexdigest()[:16]
   out.append({'key':key,'publishedAt':item['publishedAt'],'discoveredAt':item.get('discoveredAt'),'url':item.get('url'),'source':item.get('source'),'signals':sorted(added),'reason':'后续报道出现新的金额、比例或状态表述；仅为规则识别候选，需核对原文'})
 return out

def cluster(rows,stats=None):
 """Index-backed grouping with complete reference and Jaccard-prefix candidates."""
 ordered=sorted(rows,key=lambda e:(e.get('publishedAt') or 0,e['id']))
 facts={id(e):_facts(e) for e in ordered}
 frequency={}
 for fact in facts.values():
  for word in set(fact['words']):frequency[word]=frequency.get(word,0)+1
 groups=[];ref_index={};prefix_index={};prefixes={};active=deque();checks=0
 def index(gid):
  af=facts[id(groups[gid][0])]
  project=groups[gid][0]['p']
  for url in af['refs']:ref_index.setdefault((project,url),set()).add(gid)
  prefixes[gid]=_prefix_words(af['words'],frequency);digits=tuple(sorted(af['digits']))
  for word in prefixes[gid]:prefix_index.setdefault((project,digits,word),set()).add(gid)
 def unindex(gid):
  af=facts[id(groups[gid][0])]
  project=groups[gid][0]['p']
  for url in af['refs']:
   bucket=ref_index.get((project,url))
   if bucket is not None:
    bucket.discard(gid)
    if not bucket:ref_index.pop((project,url),None)
  digits=tuple(sorted(af['digits']))
  for word in prefixes.pop(gid,()):
   bucket=prefix_index.get((project,digits,word))
   if bucket is not None:
    bucket.discard(gid)
    if not bucket:prefix_index.pop((project,digits,word),None)
 for e in ordered:
  et=e.get('publishedAt') or 0
  # Input time is non-decreasing, so an anchor outside the window can never match any later event.
  while active and (groups[active[0]][0].get('publishedAt') or 0)<et-WINDOW_MS:unindex(active.popleft())
  target=None;reason=None;ef=facts[id(e)]
  if et:
   candidates=set()
   for url in ef['refs']:
    bucket=ref_index.get((e['p'],url))
    if bucket:candidates.update(bucket)
   digits=tuple(sorted(ef['digits']))
   for word in _prefix_words(ef['words'],frequency):
    bucket=prefix_index.get((e['p'],digits,word))
    if bucket:candidates.update(bucket)
   if stats is not None:checks+=len(candidates)
   for gid in sorted(candidates,reverse=True):
    # Compare to anchor only; do not chain weakly related stories across a group.
    anchor=groups[gid][0]
    reason=_match(facts[id(anchor)],ef,anchor,e)
    if reason:target=gid;break
  if target is None:
   groups.append([e])
   if et:index(len(groups)-1);active.append(len(groups)-1)
  else:groups[target].append({**e,'clusterReason':reason})
 result=[]
 for group in groups:
  first=group[0];out=dict(first)
  if len(group)>1:
   if any(item.get('providerMismatch') for item in group):out['providerMismatch']=True
   out['relatedItems']=[{k:v for k,v in e.items() if k!='relatedItems'} for e in group]
   out['progressCandidates']=progress_candidates(group)
   out['clusterSize']=len(group);out['clusterReason']='按原文引用或高度重合正文归并；不代表多方独立证实'
   sources=[]
   for e in group:
    for s in e.get('sourcesList',[]):
     if s not in sources:sources.append(s)
   out['sourcesList']=sources;out['sourceCount']=len(sources)
   out['lastRelatedAt']=max(e.get('publishedAt') or 0 for e in group)
   out['independenceNote']=out['clusterReason']
   out['revision']=hashlib.sha256('|'.join(sorted(e['id'] for e in group)).encode()).hexdigest()[:16]
  result.append(out)
 if stats is not None:stats.update(match_checks=checks,groups=len(groups))
 return sorted(result,key=lambda e:e.get('publishedAt') or 0,reverse=True)

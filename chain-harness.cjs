const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const SCRIPT_ORDER = [
 'source-status.js', 'live.js', 'project.js', 'rules.js', 'reorder.js',
 'watchlist.js', 'charts.js', 'notifications.js', 'preferences.js', 'reading-updates.js'
];

function scriptOrder() {
 const html = fs.readFileSync(path.join(__dirname, 'dist/index.html'), 'utf8');
 return [...html.matchAll(/<script\s+src="([^"]+)"/g)].map(match => match[1]);
}

function liveFixture() {
 const now = Date.now();
 const project = {id:'near', name:'NEAR Protocol', symbol:'NEAR', mark:'N',
  bg:'#e0efe8', color:'#3a7257', account:'NEARProtocol',
  website:'https://www.near.org/', team:[]};
 const news = {id:'news_0123456789ab', p:'near', type:'news', title:'Original update',
  titleZh:'中文更新', summary:'Original summary', summaryZh:null,
  publishedAt:now-3600000, discoveredAt:now-3000000, datePrecision:'source',
  source:'OpenNews', url:'https://example.org/near-news', high:true,
  topic:'产品进展', evidence:'媒体 / 聚合转述', priorityReason:'待核对原文',
  matchReason:'项目标识匹配', independenceNote:'未经独立核实',
  channel:'opennews', freshness:'recent', translationStatus:'pending',
  translationDetails:{summary:{status:'pending',retryAt:null}},
  clusterSize:2, clusterReason:'同一事件归并',
  relatedItems:[
   {source:'OpenNews', summary:'Original report', summaryZh:null,
    publishedAt:now-3600000, url:'https://example.org/near-news'},
   {source:'项目官网', summary:'Follow-up report', summaryZh:'后续报道',
    publishedAt:now-1800000, url:'https://example.org/follow-up'}
  ],
  progressCandidates:[{key:'update-1', source:'项目官网',
   publishedAt:now-1800000, url:'https://example.org/follow-up',
   reason:'新增状态', signals:['已上线']}],
  sourcesList:[{name:'OpenNews', url:'https://example.org/near-news', channel:'opennews'}]
 };
 const market = {symbol:'NEARUSDT', source:'Binance', fetchedAt:now,
  price:5, priceAt:now, change24h:2, oi:100, oiAt:now,
  oiFrom:now-3600000, oiChange1h:2, ema200:4, ema360:3,
  close4h:5, candleAt:now-1000, klineCount:400, errors:{},
  candles:[{time:now-8*3600000, closeTime:now-4*3600000-1,
   open:4, high:5, low:3, close:4.5, volume:10},
   {time:now-4*3600000, closeTime:now-1000,
    open:4.5, high:6, low:4, close:5, volume:11}]
 };
 const rule = {id:'rule-1', p:'near', type:'news', name:'重点消息',
  period:'4h', threshold:5, cooldownMinutes:60, on:true, createdAt:now-7200000};
 const alert = {id:'alert-1', p:'near', type:'news', ruleName:'重点消息',
  title:'Original update', at:now-60000,
  evidence:{source:'OpenNews', eventId:news.id, url:news.url}};
 return {projects:[project], markets:{near:market}, events:[news], sources:{near:{}},
  social:{}, updatedAt:now, collectors:{},
  alertState:{rules:[rule], runtime:{'rule-1':{status:'watching',checkedAt:now}}, alerts:[alert]},
  serverTime:now, translation:{status:'available'}, cadence:{marketSeconds:60,newsSeconds:1800}};
}

function chartFixture() {
 const now = Date.now();
 return {period:'4h', fetchedAt:now, warmupCount:400,
  candles:[{time:now-8*3600000,closeTime:now-4*3600000-1,
   open:4,high:5,low:3,close:4.5,ema200:4,ema360:3},
   {time:now-4*3600000,closeTime:now-1000,
   open:4.5,high:6,low:4,close:5,ema200:4,ema360:3}]};
}

function createHarness(options={}) {
 assert.deepEqual(scriptOrder(), SCRIPT_ORDER, 'index.html script order changed');
 const nodes = new Map(), created = [], requests = [], storage = new Map(Object.entries(options.storage || {}));
 const documentHandlers = new Map(), windowHandlers = new Map(), intervals = [];
 const live = options.live || liveFixture(), chart = options.chart || chartFixture();
 let serial = 0;
 function element(key) {
  const calls = [], children = [], listeners = new Map(), attributes = new Map();
  const classes = new Set();
  let html = '', explicitText, outer = '', className = '';
  const item = {key, calls, children, listeners, dataset:{}, style:{},
   hidden:false, value:'', checked:false, open:false, disabled:false,
   removed:false, offsetHeight:40, scrollLeft:0, scrollTop:0,
   get innerHTML(){return html},
   set innerHTML(value){html=String(value);explicitText=undefined;calls.push(['innerHTML',html])},
   get textContent(){return explicitText===undefined?html.replace(/<[^>]*>/g,''):explicitText},
   set textContent(value){explicitText=String(value);html='';calls.push(['textContent',explicitText])},
   get outerHTML(){return outer},
   set outerHTML(value){outer=String(value);calls.push(['outerHTML',outer])},
   get className(){return className},
   set className(value){className=String(value);classes.clear();className.split(/\s+/).filter(Boolean).forEach(x=>classes.add(x))},
   classList:{
    add(...values){values.forEach(value=>classes.add(value));className=[...classes].join(' ')},
    remove(...values){values.forEach(value=>classes.delete(value));className=[...classes].join(' ')},
    contains(value){return classes.has(value)},
    toggle(value,force){const next=force===undefined?!classes.has(value):Boolean(force);
     if(next)classes.add(value);else classes.delete(value);className=[...classes].join(' ');return next}
   },
   addEventListener(type,fn){if(!listeners.has(type))listeners.set(type,[]);listeners.get(type).push(fn)},
   removeEventListener(type,fn){listeners.set(type,(listeners.get(type)||[]).filter(x=>x!==fn))},
   append(...items){children.push(...items);calls.push(['append',...items])},
   appendChild(child){children.push(child);calls.push(['appendChild',child]);return child},
   prepend(...items){children.unshift(...items);calls.push(['prepend',...items])},
   before(...items){calls.push(['before',...items])},
   remove(){item.removed=true;calls.push(['remove'])},
   insertAdjacentHTML(position,value){const text=String(value);calls.push(['insertAdjacentHTML',position,text]);
    if(position==='afterbegin')html=text+html;else if(position==='beforeend')html+=text},
   setAttribute(name,value){attributes.set(name,String(value));calls.push(['setAttribute',name,String(value)])},
   getAttribute(name){return attributes.get(name)??null},
   hasAttribute(name){return attributes.has(name)},
   focus(){calls.push(['focus'])}, close(){item.open=false;calls.push(['close'])},
   showModal(){item.open=true;calls.push(['showModal'])},
   matches(){return false},
   closest(selector){return key.includes('.account-grid')&&selector==='.project-section'
    ?node('#project-overview .project-section'):null},
   getBoundingClientRect(){return {left:0,top:0,right:300,bottom:40,width:300,height:40}},
   scrollIntoView(){calls.push(['scrollIntoView'])},
   setPointerCapture(){calls.push(['setPointerCapture'])},
   contains(other){return children.includes(other)},
   querySelector(selector){return node(key+' '+selector)},
   querySelectorAll(selector){return selector==='.account-card'?[]:queryAll(selector)}
  };
  return item;
 }
 function node(selector){if(!nodes.has(selector))nodes.set(selector,element(selector));return nodes.get(selector)}
 const views=['feed','saved','rules'].map(view=>{const item=element('[data-view] '+view);item.dataset.view=view;return item});
 const filters=['all','news','market','combo'].map(filter=>{const item=element('[data-filter] '+filter);item.dataset.filter=filter;return item});
 const rails=[element('.rail-block 0'),element('.rail-block 1')];
 const dialogs=[node('#detail-dialog'),node('#form-dialog')];
 const accountGrids=[element('#project-overview .account-grid 0'),element('#project-overview .account-grid 1')];
 function queryAll(selector){
  if(selector==='.rail-block')return rails;
  if(selector==='[data-view]')return views;
  if(selector==='[data-filter]')return filters;
  if(selector==='dialog')return dialogs;
  if(selector==='#project-overview .account-grid')return accountGrids;
  if(selector==='#detail-content .quality-evidence')return created.filter(item=>!item.removed&&item.classList.contains('quality-evidence'));
  if(selector==='.alert-history details'){
   const count=(node('#feed').innerHTML.match(/<details\b/g)||[]).length;
   return Array.from({length:count},(_,i)=>node('.alert-history details '+i));
  }
  return [];
 }
 function addHandler(map,type,fn,capture=false){if(!map.has(type))map.set(type,[]);map.get(type).push({fn,capture})}
 const document={visibilityState:'visible',hidden:false,activeElement:{tagName:'BODY'},
  addEventListener(type,fn,capture){addHandler(documentHandlers,type,fn,Boolean(capture))},
  removeEventListener(type,fn){documentHandlers.set(type,(documentHandlers.get(type)||[]).filter(x=>x.fn!==fn))},
  querySelector:node,querySelectorAll:queryAll,
  getElementById(id){return created.find(item=>item.id===id&&!item.removed)||node('#'+id)},
  createElement(tag){const item=element('created '+(++serial)+' '+tag);item.tagName=tag.toUpperCase();created.push(item);return item},
  elementFromPoint(){return null}
 };
 node('#rule-form').elements={type:{value:'ema',addEventListener(){}},
  period:{value:'4h'},threshold:{value:'5',required:true},
  name:{value:''},cooldownMinutes:{value:'60'}};
 node('#backend-rule-form').elements={type:{value:'ema'},period:{value:'4h'},
  threshold:{value:'5'},p:{value:'near'},name:{value:''},cooldownMinutes:{value:'60'}};
 const window={innerWidth:1200,innerHeight:800,isSecureContext:false,
  addEventListener(type,fn){addHandler(windowHandlers,type,fn)},
  dispatchEvent(event){for(const {fn} of windowHandlers.get(event.type)||[])fn(event)},
  focus(){},toastTimer:0};
 const localStorage={getItem:key=>storage.get(key)||null,
  setItem(key,value){storage.set(key,String(value))},removeItem:key=>storage.delete(key)};
 const fetch=async(url,init={})=>{
  requests.push({url:String(url),init});
  let value,ok=true;
  if(String(url)==='/api/live')value=live;
  else if(String(url).startsWith('/api/chart?'))value=chart;
  else if(String(url)==='/api/preferences')value=init.method==='POST'
   ?{values:JSON.parse(init.body).values}:{values:{}};
  else {ok=false;value={error:'unhandled route'}}
  return {ok,status:ok?200:404,json:async()=>value};
 };
 class FakeFormData {
  constructor(form){this.values=form?.formData||{}}
  *[Symbol.iterator](){yield* Object.entries(this.values)}
  get(name){return this.values[name]??null}
 }
 const ctx={console,URL,document,window,localStorage,fetch,FormData:FakeFormData,
  navigator:{},setTimeout(){return ++serial},clearTimeout(){},
  setInterval(fn){intervals.push(fn);return ++serial},
  CustomEvent:class{constructor(type,init){this.type=type;this.detail=init?.detail}}};
 vm.createContext(ctx);
 for(const name of SCRIPT_ORDER)vm.runInContext(fs.readFileSync(path.join(__dirname,'dist',name),'utf8'),ctx,{filename:name});
 const evalInPage=source=>vm.runInContext(source,ctx);
 async function settle(){for(let i=0;i<4;i++)await new Promise(resolve=>setImmediate(resolve))}
 function dispatch(type,target,extra={}){
  let stopped=false;
  const event={target,preventDefault(){},stopPropagation(){},
   stopImmediatePropagation(){stopped=true},...extra};
  const handlers=(documentHandlers.get(type)||[]).slice().sort((a,b)=>Number(b.capture)-Number(a.capture));
  for(const {fn} of handlers){if(stopped)break;fn(event)}
  return event;
 }
 return {ctx,nodes,created,requests,storage,documentHandlers,windowHandlers,
  intervals,live,chart,rails,views,filters,node,queryAll,evalInPage,settle,dispatch};
}

module.exports={SCRIPT_ORDER,scriptOrder,liveFixture,chartFixture,createHarness};

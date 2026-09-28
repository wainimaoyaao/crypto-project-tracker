const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
const source=fs.readFileSync('dist/live.js','utf8');
function elementStub(){
 return {textContent:'',innerHTML:'',hidden:false,value:'',checked:false,className:'',open:false,
  classList:{add(){},remove(){},toggle(){}},addEventListener(){},removeEventListener(){},
  querySelector:()=>elementStub(),querySelectorAll:()=>[],append(){},appendChild(){},setAttribute(){},getAttribute:()=>null,
  hasAttribute:()=>false,focus(){},close(){},showModal(){},remove(){},matches:()=>false,closest:()=>null,
  getBoundingClientRect:()=>({left:0,top:0,right:0,bottom:0})};
}
function loadLive(){
 const pending=[];
 const ctx={
  console,setTimeout:()=>0,clearTimeout(){},setInterval:()=>0,URL,FormData:function(){},
  fetch:(url,opts)=>new Promise((resolve,reject)=>pending.push({resolve,reject,url})),
  CustomEvent:class{constructor(type,opts){this.type=type;this.detail=opts&&opts.detail}},
  localStorage:{getItem:()=>null,setItem(){}},
  providerHealth:()=>'来源覆盖',
  sourceHealth:()=>({label:'正常'}),
  window:{dispatchEvent(){},addEventListener(){},toastTimer:0},
  document:{activeElement:{tagName:'BODY'},visibilityState:'visible',
   addEventListener(){},
   createElement:()=>elementStub(),
   querySelector:()=>elementStub(),
   querySelectorAll:sel=>sel==='.rail-block'?[elementStub(),elementStub()]:[]}
 };
 vm.createContext(ctx);
 const api=vm.runInContext(source+';({refreshLive,getState:()=>liveData,getEvents:()=>events,getError:()=>liveError})',ctx);
 return {ctx,api,pending};
}
function okBody(marker){
 return {projects:[{id:'near',name:'NEAR',symbol:'NEAR',mark:'N',bg:'#eee',color:'#333',account:'NEARProtocol'}],
  events:[{id:'news_0123456789ab',p:'near',type:'news',title:'E '+marker,summary:'s',publishedAt:1e12}],
  markets:{},sources:{},social:{},alertState:{rules:[],alerts:[]},serverTime:marker,cadence:{},translation:{}};
}
const ok=marker=>({ok:true,json:async()=>okBody(marker)});
const tick=()=>new Promise(r=>setTimeout(r,0));
test('stale in-flight responses cannot overwrite a newer refresh',async()=>{
 const {api,pending}=loadLive();
 pending.shift().resolve(ok('initial'));await tick();
 const first=api.refreshLive(),second=api.refreshLive();
 assert.equal(pending.length,2);
 pending[1].resolve(ok('newest'));await second;
 pending[0].resolve(ok('stale'));await first;
 await tick();
 assert.equal(api.getState().serverTime,'newest');
 assert.equal(api.getEvents()[0].title,'E newest');
});
test('a late failure cannot replace newer state',async()=>{
 const {api,pending}=loadLive();
 pending.shift().resolve(ok('initial'));await tick();
 const first=api.refreshLive(),second=api.refreshLive();
 pending[1].resolve(ok('newest'));await second;
 pending[0].reject(new Error('network down'));await first;
 await tick();
 assert.equal(api.getState().serverTime,'newest');
 assert.equal(api.getError(),'');
});
test('in-order refreshes still apply',async()=>{
 const {api,pending}=loadLive();
 pending.shift().resolve(ok('initial'));await tick();
 const first=api.refreshLive(),second=api.refreshLive();
 pending[0].resolve(ok('first'));await first;
 pending[1].resolve(ok('second'));await second;
 await tick();
 assert.equal(api.getState().serverTime,'second');
});

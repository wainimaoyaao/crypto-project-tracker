const test = require('node:test');
const assert = require('node:assert/strict');
const { createHarness } = require('./chain-harness.cjs');

test('news detail composes quality evidence and the reading timeline', async () => {
 const page = createHarness();
 await page.settle();
 assert.equal(page.evalInPage('typeof registerDetailExtension'), 'function');
 assert.equal(page.evalInPage('detailExtensions.beforeOpen.length'), 1);
 assert.equal(page.evalInPage('detailExtensions.afterOpen.length'), 4);

 const newsId = page.evalInPage("events.find(event => event.type === 'news').id");
 page.evalInPage(`openDetail(${newsId})`);

 const evidence = page.created.find(node => node.className === 'quality-evidence' && !node.removed);
 assert.ok(evidence, 'news detail adds quality evidence');
 assert.match(evidence.textContent, /为什么出现在这里/);
 assert.match(evidence.textContent, /项目标识匹配/);

 const footerCalls = page.node('#detail-content .modal-footer').calls;
 const additions = footerCalls
  .filter(call => call[0] === 'insertAdjacentHTML')
  .map(call => call[2])
  .join('');
 assert.match(additions, /translation-note/);
 assert.match(additions, /同一事件的时间线/);
 assert.match(additions, /新增进展/);

 const readingLedger = JSON.parse(page.storage.get('signal-reading-v2'));
 assert.equal(readingLedger.versions[newsId], 'update-1');

 const evidenceCount = page.created.filter(node => node.className === 'quality-evidence').length;
 const marketId = page.evalInPage("events.find(event => event.type === 'market').id");
 page.evalInPage(`openDetail(${marketId})`);
 assert.match(page.node('#detail-content').innerHTML, /行情快照/);
 assert.match(page.node('#detail-content').innerHTML, /Binance/);
 assert.equal(
  page.created.filter(node => node.className === 'quality-evidence').length,
  evidenceCount,
  'market detail does not add news-quality sections'
 );
});

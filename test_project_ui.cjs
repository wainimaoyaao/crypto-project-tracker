const test = require('node:test');
const assert = require('node:assert/strict');
const { createHarness } = require('./chain-harness.cjs');

const NEWS_ID = 0x0123456789ab;

function button(dataset) {
 const item = {
  dataset,
  closest(selector) { return selector === 'button' ? item : null; },
  hasAttribute(name) {
   const key = name.replace(/^data-/, '').replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
   return Object.prototype.hasOwnProperty.call(dataset, key);
  }
 };
 return item;
}

test('project UI composes event cards, original text switching, and add-project form', async () => {
 const page = createHarness({
  storage: {
   'signal-live-v1': JSON.stringify({ projects: ['near'], read: [NEWS_ID] }),
   'signal-reading-v2': JSON.stringify({ lastVisit: Date.now() - 60_000, versions: { [NEWS_ID]: '' } })
  }
 });
 await page.settle();

 const card = page.evalInPage("eventCard(events.find(event => event.type === 'news'))");
 assert.match(card, /language-toggle/);
 assert.match(card, /后续进展候选 1/);
 assert.match(card, /2 条相关报道 · 已合并/);
 assert.match(card, /已读事件有新增进展/);
 assert.match(card, /中文更新/);

 page.dispatch('click', button({ original: String(NEWS_ID) }));
 await page.settle();
 const originalCard = page.evalInPage("eventCard(events.find(event => event.type === 'news'))");
 assert.match(originalCard, /Original update/);
 assert.match(originalCard, /显示中文/);

 page.evalInPage('openAdd()');
 assert.equal(page.node('#form-dialog').open, true);
 assert.match(page.node('#form-content').innerHTML, /新增关注项目/);
 assert.match(page.node('#form-content').innerHTML, /data-manual-project/);

 page.evalInPage("state.project='near';state.view='feed';render()");
 assert.match(page.node('#project-overview').innerHTML, /团队成员的 X 账号/);
 assert.match(page.node('#project-overview').innerHTML, /account-grid/);
});

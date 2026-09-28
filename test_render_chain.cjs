const test = require('node:test');
const assert = require('node:assert/strict');
const { createHarness } = require('./chain-harness.cjs');

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

test('the loaded render chain preserves feed, project, and rule surfaces', async () => {
 const page = createHarness();
 await page.settle();
 assert.equal(page.evalInPage('typeof registerRenderExtension'), 'function');
 assert.equal(page.evalInPage('renderExtensions.length'), 4);
 assert.equal(page.evalInPage("renderExtensions.map(extension=>extension.name).join(',')"), 'renderLiveStatus,renderProjectPage,renderPreferenceStatus,renderReadingPage');
 assert.equal(page.evalInPage('typeof registerProjectPageExtension'), 'function');
 assert.equal(page.evalInPage('projectPageExtensions.length'), 1);

 assert.equal(page.node('.demo-status').textContent, '◌ 真实数据测试');
 assert.match(page.node('.demo-banner').innerHTML, /LIVE BETA/);
 assert.match(page.node('.brief').innerHTML, /DATA COVERAGE/);
 assert.match(page.node('#market-watch').innerHTML, /data-project=\"near\"/);
 assert.match(page.node('#feed').innerHTML, /catchup-panel/);
 assert.match(page.node('#feed').innerHTML, /translation-note/);
 assert.match(page.node('#feed').innerHTML, /已合并/);
 assert.equal(page.node('footer span').textContent, '阅读偏好已同步');

 page.dispatch('click', button({ project: 'near' }));
 await page.settle();
 assert.match(page.node('#project-overview').innerHTML, /project-head/);
 assert.match(page.node('#project-overview > .project-section').outerHTML, /linked-chart/);
 assert.match(page.node('#project-overview > .project-section').outerHTML, /chart-news-marker/);

 page.dispatch('click', button({ view: 'rules' }));
 await page.settle();
 assert.match(page.node('#feed').innerHTML, /1 条后台规则/);
 assert.match(page.node('#feed').innerHTML, /触发记录/);

 const notificationPanel = page.created.find(node => node.id === 'browser-notifications');
 assert.ok(notificationPanel, 'rules view adds a browser-notification panel');
 assert.match(notificationPanel.children[0].textContent, /当前浏览器不支持此功能。/);
});

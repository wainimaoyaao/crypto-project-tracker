const test = require('node:test');
const assert = require('node:assert/strict');
const { createHarness } = require('./chain-harness.cjs');

test('rules view composes backend rules, history context, and rule forms', async () => {
 const page = createHarness();
 await page.settle();
 assert.equal(page.evalInPage('typeof registerRulePageExtension'), 'function');
 assert.equal(page.evalInPage('rulePageExtensions.length'), 1);
 assert.equal(page.windowHandlers.get('signal-live').length, 1);
 assert.equal(page.windowHandlers.get('storage').length, 1);

 page.evalInPage("state.view='rules';state.project=null;render()");
 const rulesPage = page.node('#feed').innerHTML;
 assert.match(rulesPage, /1 条后台规则/);
 assert.match(rulesPage, /重点消息/);
 assert.match(rulesPage, /触发记录/);

 const historyCalls = page.node('.alert-history details 0').calls
  .filter(call => call[0] === 'insertAdjacentHTML')
  .map(call => call[2])
  .join('');
 assert.match(historyCalls, /查看事件与原文/);

 const notificationPanel = page.created.find(node => node.id === 'browser-notifications');
 assert.ok(notificationPanel, 'rules view adds the notification panel');
 assert.match(notificationPanel.children[0].textContent, /当前浏览器不支持此功能。/);
 assert.equal(notificationPanel.children[1].disabled, true);

 page.evalInPage('openRule()');
 assert.equal(page.node('#form-dialog').open, true);
 assert.match(page.node('#form-content').innerHTML, /新建后台规则/);
 assert.match(page.node('#backend-rule-description').textContent, /EMA 200/);
 assert.equal(page.node('#backend-threshold').hidden, true);

 page.evalInPage("openRule('rule-1')");
 assert.match(page.node('#form-content').innerHTML, /编辑后台规则/);
 assert.match(page.node('#form-content').innerHTML, /重点消息/);
});

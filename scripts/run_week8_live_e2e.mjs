// The console submits via real HTTP. Only the backend OCR controller may click the fixture.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { mkdir, writeFile, readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';
import { chromium } from '/Users/ziang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';

const root = resolve(import.meta.dirname, '..');
const out = resolve(root, 'output/week8/live_e2e');
const base = 'http://127.0.0.1:8765';
const evidence = { checked_at: new Date().toISOString(), cases: [], requests: [],
  execution: 'Real MSS, EasyOCR, PyAutoGUI and local HTTP; deterministic local test page',
  browser: 'Headless console plus visible Chrome target; no mocked executor or target click' };
let backend, browser, desktop, fixtureServer, page, fixture;
let backendLog = '';
const pendingResponses = [];

async function shot(target, name) {
  await target.screenshot({ path: resolve(out, `${name}.png`), fullPage: true });
}
async function submit(task, mode = 'live') {
  await page.getByLabel('任务内容').fill(task);
  await page.getByRole('button', { name: mode === 'live' ? '实时' : '预览', exact: true }).click();
  const responsePromise = page.waitForResponse(r => r.url() === `${base}/api/tasks` && r.request().method() === 'POST');
  await page.getByRole('button', { name: '开始任务' }).click();
  const response = await responsePromise;
  assert.equal(response.status(), 202);
  const body = await response.json();
  return body.task.id;
}
async function terminal(id) {
  await page.waitForFunction(() => ['执行完成', '预览完成', '已结束'].includes(document.querySelector('#livePill').textContent),
    null, { timeout: 150000 });
  // Read-only HTTP inspection supplements the UI trigger, never substitutes for it.
  const record = await fetch(`${base}/api/tasks/${id}`).then(r => r.json());
  await writeFile(resolve(out, `task_${id}.json`), JSON.stringify(record, null, 2));
  const events = await readFile(resolve(root, `output/local_bridge/${id}/events.jsonl`), 'utf8');
  await writeFile(resolve(out, `events_${id}.jsonl`), events);
  return { task: record.task, events: events.trim().split('\n').map(line => JSON.parse(line)) };
}
async function resetFixture(query = '') {
  await fixture.goto(`http://127.0.0.1:18765/${query}`);
  await fixture.bringToFront();
  await delay(800);
  assert.equal(await fixture.locator('#result').textContent(), 'READY');
  assert.equal(await fixture.evaluate(() => window.clickCount), 0);
}
async function caseResult(id, fn) {
  const started = Date.now();
  const data = await fn();
  evidence.cases.push({ id, result: 'passed', elapsed_seconds: (Date.now() - started) / 1000, ...data });
  console.log(`${id}: passed`);
}
try {
  await mkdir(out, { recursive: true });
  // Do not accidentally reuse an existing bridge with different permissions.
  const occupied = await fetch(`${base}/api/health`, { signal: AbortSignal.timeout(600) }).then(() => true).catch(() => false);
  assert.equal(occupied, false, 'Port 8765 already in use; stop that service before running this isolated test');
  fixtureServer = createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' });
    res.end(`<!doctype html><html><head><title>GUI Agent safe click test</title><style>
      body{font-family:Arial,sans-serif;background:white;color:black;margin:80px;text-align:center}
      h1{font-size:32px}button{font:56px Arial;padding:35px 70px;margin:30px;background:#eee;border:3px solid black}
      #result{font:64px Arial;margin:60px}</style></head><body>
      <h1>GUI Agent Week 8</h1><button id="target">VERIFY</button>
      ${req.url.includes('duplicate') ? '<button>VERIFY</button>' : ''}
      <div id="result">READY</div><script>window.clickCount=0;
      document.querySelector('#target').addEventListener('click',()=>{window.clickCount++;
      document.querySelector('#result').textContent='VERIFIED';document.querySelector('#target').textContent='FINISHED';
      document.querySelector('#target').disabled=true;});</script></body></html>`);
  });
  await new Promise((ok, fail) => { fixtureServer.once('error', fail); fixtureServer.listen(18765, '127.0.0.1', ok); });
  backend = spawn(resolve(root, '.venv/bin/python'), ['-u', 'scripts/run_local_executor.py', '--enable-live'],
    { cwd: root, stdio: ['ignore', 'pipe', 'pipe'] });
  backend.stdout.on('data', b => backendLog += b);
  backend.stderr.on('data', b => backendLog += b);
  let healthy = false;
  for (let n = 0; n < 60; n++) {
    healthy = await fetch(`${base}/api/health`).then(r => r.json()).then(v => v.live_enabled === true).catch(() => false);
    if (healthy) break;
    if (backend.exitCode !== null) throw new Error(`Backend exited ${backend.exitCode}: ${backendLog}`);
    await delay(200);
  }
  assert(healthy);
  const executablePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  browser = await chromium.launch({ headless: true, executablePath });
  desktop = await chromium.launch({ headless: false, executablePath,
    args: ['--window-position=0,25', '--window-size=1470,900', '--no-first-run', '--no-default-browser-check'] });
  fixture = await desktop.newPage({ viewport: null });
  await resetFixture();
  await shot(fixture, '01_target_before');
  page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  page.on('response', response => {
    if (response.url().startsWith(`${base}/api/`)) pendingResponses.push((async () => {
      let body;
      try { body = response.headers()['content-type']?.includes('json') ? await response.json() : '[PNG image]'; }
      catch { body = '[body unavailable]'; }
      evidence.requests.push({ method: response.request().method(), path: new URL(response.url()).pathname,
        status: response.status(), input: response.request().postData(), body });
    })());
  });
  await page.goto(base);
  await page.getByText('本地执行器已连接 · 实时已开启').waitFor();

  await caseResult('real_live_click_success', async () => {
    const input = '点击 VERIFY，确认出现 VERIFIED';
    const id = await submit(input);
    const { task, events } = await terminal(id);
    assert.equal(task.mode, 'live'); assert.equal(task.status, 'done');
    assert.equal(task.result.action_count, 1);
    assert.equal(task.result.completion_check.success, true);
    assert.deepEqual(task.result.completion_check.evidence.matched_text, ['VERIFIED']);
    assert.equal(await fixture.evaluate(() => window.clickCount), 1);
    assert.equal(await fixture.locator('#result').textContent(), 'VERIFIED');
    assert(events.some(v => v.event === 'action_started'));
    assert(events.some(v => v.event === 'loop_completed'));
    await page.getByText('已确认出现“VERIFIED”', { exact: true }).waitFor();
    assert.equal(await page.locator('#safetyMetric').textContent(), '通过');
    assert.match(await page.locator('#confidenceMetric').textContent(), /%/);
    await page.locator('#captureNote').getByText('截图已加载').waitFor();
    await shot(page, '02_console_live_success'); await shot(fixture, '03_target_after');
    return { input, task_id: id, backend_status: task.status, action_count: 1,
      target_dom: 'VERIFIED', target_click_count: 1, expected_ocr: 'VERIFIED',
      completion_check: task.result.completion_check, duration_seconds: task.result.duration_seconds };
  });
  await caseResult('completion_text_missing', async () => {
    await resetFixture();
    const id = await submit('点击 VERIFY，确认出现 MISSING');
    const { task } = await terminal(id);
    assert.equal(task.status, 'action_failed'); assert.equal(task.result.action_count, 1);
    assert.equal(await fixture.evaluate(() => window.clickCount), 1);
    assert.match(await page.locator('#runNote').textContent(), /MISSING/);
    await shot(page, '04_expected_result_missing');
    return { task_id: id, backend_status: task.status, action_count: 1, error: task.error };
  });
  await caseResult('ambiguous_target_no_action', async () => {
    await resetFixture('?duplicate');
    const id = await submit('点击 VERIFY');
    const { task } = await terminal(id);
    assert.equal(task.status, 'stopped'); assert.equal(task.result.action_count, 0);
    assert.equal(await fixture.evaluate(() => window.clickCount), 0);
    assert.match(task.error, /无法唯一定位/);
    return { task_id: id, backend_status: task.status, action_count: 0, error: task.error };
  });
  await caseResult('active_task_poll_timeout_and_recovery', async () => {
    await resetFixture();
    let injected = 0;
    await page.route('**/api/tasks/*', async route => {
      if (/\/api\/tasks\/[a-f0-9]{12}$/.test(new URL(route.request().url()).pathname)) {
        injected++; await delay(6500); try { await route.abort('timedout'); } catch {}
      } else await route.continue();
    });
    const id = await submit('点击 VERIFY', 'preview');
    await page.getByRole('button', { name: '恢复状态读取' }).waitFor({ timeout: 12000 });
    assert(await page.getByRole('button', { name: '开始任务' }).isDisabled());
    await shot(page, '05_poll_timeout');
    await page.unrouteAll({ behavior: 'ignoreErrors' });
    await page.getByRole('button', { name: '恢复状态读取' }).click();
    const { task } = await terminal(id);
    assert.equal(task.status, 'preview_ready');
    assert.equal(await fixture.evaluate(() => window.clickCount), 0);
    return { task_id: id, injection: 'browser GET delayed past 5000 ms; real backend still processes',
      injected_requests: injected, recovered_same_task: true, status: task.status };
  });
  await caseResult('screenshot_unavailable_and_manual_recovery', async () => {
    const id = evidence.cases.at(-1).task_id;
    await page.route('**/screenshot?**', route => route.fulfill({ status: 404, body: 'injected image failure' }));
    // A real UI recovery control issues the resource request; no direct renderTask call.
    await page.evaluate(() => { document.querySelector('#localScreenImage').src += '&retry=1'; });
    await page.getByRole('button', { name: '重试截图' }).waitFor();
    await page.getByRole('button', { name: '重试截图' }).click();
    await page.locator('#captureNote').getByText('截图加载失败').waitFor();
    await page.unrouteAll({ behavior: 'ignoreErrors' });
    await page.getByRole('button', { name: '重试截图' }).click();
    await page.locator('#captureNote').getByText('截图已加载').waitFor();
    return { task_id: id, injection: 'browser screenshot HTTP 404 until fault removed', status: 'image recovered' };
  });
  await caseResult('active_poll_disconnect_and_recovery', async () => {
    await page.route('**/api/tasks/*', route => /\/api\/tasks\/[a-f0-9]{12}$/.test(new URL(route.request().url()).pathname)
      ? route.abort('connectionrefused') : route.continue());
    const id = await submit('点击 VERIFY', 'preview');
    await page.getByRole('button', { name: '恢复状态读取' }).waitFor();
    assert.match(await page.locator('#overviewStatus').textContent(), /未连接/);
    assert(await page.getByRole('button', { name: '开始任务' }).isDisabled());
    await page.unrouteAll({ behavior: 'ignoreErrors' });
    await page.getByRole('button', { name: '恢复状态读取' }).click();
    const { task } = await terminal(id);
    assert.equal(task.status, 'preview_ready');
    return { task_id: id, injection: 'browser task-poll connection refused; backend kept alive',
      recovered_same_task: true, status: task.status };
  });
  await caseResult('mobile_320_long_task', async () => {
    await page.setViewportSize({ width: 320, height: 900 });
    const longInput = '点击 VERIFY，确认出现 VERIFIED。' + '窄屏长文案验证'.repeat(28);
    assert(longInput.length <= 240);
    const id = await submit(longInput, 'preview');
    const { task } = await terminal(id);
    assert.equal(task.status, 'preview_ready');
    const sizes = await page.evaluate(() => ({ viewport: innerWidth, content: document.documentElement.scrollWidth }));
    assert(sizes.content <= 321);
    const controls = await page.locator('#taskForm button').evaluateAll(nodes => nodes.map(n => {
      const r = n.getBoundingClientRect(); return { left: r.left, right: r.right };
    }));
    assert(controls.every(r => r.left >= 0 && r.right <= 321));
    await shot(page, '06_mobile_320');
    return { task_id: id, input_length: longInput.length, ...sizes };
  });
  evidence.result = 'passed';
} catch (error) {
  evidence.result = 'failed'; evidence.error = error.stack || String(error); console.error(evidence.error);
  if (page) await shot(page, 'failure_console').catch(() => {});
  if (fixture) await shot(fixture, 'failure_target').catch(() => {});
  process.exitCode = 1;
} finally {
  await Promise.allSettled(pendingResponses);
  if (desktop) await desktop.close();
  if (browser) await browser.close();
  if (backend && backend.exitCode === null) {
    backend.kill('SIGINT');
    await Promise.race([new Promise(ok => backend.once('exit', ok)), delay(3000)]);
    if (backend.exitCode === null) backend.kill('SIGTERM');
  }
  if (fixtureServer) await new Promise(ok => fixtureServer.close(ok));
  await writeFile(resolve(out, 'backend.log'), backendLog);
  await writeFile(resolve(out, 'results.json'), JSON.stringify(evidence, null, 2));
  console.log(JSON.stringify({ result: evidence.result, cases: evidence.cases.length, output: out }));
}

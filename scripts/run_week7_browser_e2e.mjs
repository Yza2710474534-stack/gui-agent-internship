import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve, relative } from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';
import { chromium } from '/Users/ziang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';

const project = resolve(import.meta.dirname, '..');
const output = resolve(project, process.env.GUI_AGENT_E2E_OUTPUT || 'output/week7/browser_e2e');
const base = 'http://127.0.0.1:8765';
const python = resolve(project, '.venv/bin/python');
const script = resolve(project, 'scripts/run_local_executor.py');
const results = { checked_at: new Date().toISOString(), browser: 'Google Chrome headless via Playwright',
  backend: 'real local bridge and LocalExecutor, preview only', cases: [], widths: [], requests: [],
  screenshots: [], backend_log: relative(project, resolve(output, 'backend.log')) };
let backend;
let backendLog = '';
let browser;

async function waitForHealth(timeout = 12000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    if (backend?.exitCode !== null) throw new Error(`backend exited: ${backend.exitCode}`);
    try { const response = await fetch(`${base}/api/health`, { signal: AbortSignal.timeout(800) }); if (response.ok) return; }
    catch { /* startup */ }
    await delay(200);
  }
  throw new Error('backend health did not become ready');
}

function startBackend() {
  backend = spawn(python, [script], { cwd: project, stdio: ['ignore', 'pipe', 'pipe'] });
  backend.stdout.on('data', bytes => { backendLog += bytes.toString(); });
  backend.stderr.on('data', bytes => { backendLog += bytes.toString(); });
}

async function stopBackend() {
  if (!backend || backend.exitCode !== null) return;
  const child = backend;
  child.kill('SIGINT');
  await Promise.race([new Promise(resolveExit => child.once('exit', resolveExit)), delay(3000)]);
  if (child.exitCode === null) { child.kill('SIGTERM'); await delay(400); }
  backend = null;
}

async function screenshot(page, name) {
  const path = resolve(output, `${name}.png`);
  await page.screenshot({ path, fullPage: true, animations: 'disabled' });
  results.screenshots.push(relative(project, path));
}

async function newPage(width = 1280) {
  const page = await browser.newPage({ viewport: { width, height: 900 }, deviceScaleFactor: 1 });
  page.on('response', response => {
    const url = new URL(response.url());
    if (url.origin === base && url.pathname.startsWith('/api/')) {
      results.requests.push({ method: response.request().method(), path: url.pathname,
        status: response.status(), resource_type: response.request().resourceType() });
    }
  });
  await page.goto(base, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => document.querySelector('#connectionState')?.textContent?.includes('本地执行器已连接'),
    { timeout: 10000 });
  return page;
}

async function submitPreview(page) {
  await page.getByLabel('任务内容').fill('搜索 GUI Agent');
  await page.getByRole('button', { name: '预览', exact: true }).click();
  await page.getByRole('button', { name: '开始任务' }).click();
  await page.locator('#livePill').getByText('预览完成').waitFor({ timeout: 120000 });
  const taskId = await page.locator('#requestMeta').textContent().then(value => value.match(/任务 ([a-f0-9]{12})/)?.[1]);
  assert.match(taskId ?? '', /^[a-f0-9]{12}$/);
  await page.locator('#captureNote').getByText('截图已加载').waitFor({ timeout: 12000 });
  return { task_id: taskId, status: await page.locator('#overviewStatus').textContent(),
    ocr: await page.locator('#ocrMetric').textContent(), screenshot: await page.locator('#captureNote').textContent() };
}

try {
  await mkdir(output, { recursive: true });
  startBackend();
  await waitForHealth();
  browser = await chromium.launch({ headless: true,
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    args: ['--no-first-run', '--no-default-browser-check'] });

  const page = await newPage();
  const success = await submitPreview(page);
  assert.equal(success.status, '动作方案已生成');
  assert.match(success.ocr, /\d+ 项/);
  assert(results.requests.some(r => r.method === 'POST' && r.path === '/api/tasks' && r.status === 202));
  assert(results.requests.some(r => r.method === 'GET' && r.path === `/api/tasks/${success.task_id}` && r.status === 200));
  assert(results.requests.some(r => r.path === `/api/tasks/${success.task_id}/screenshot` && r.status === 200));
  await screenshot(page, '01_preview_success_1280');
  results.cases.push({ id: 'preview_success', type: 'browser E2E / actual screenshot and OCR', result: 'passed', ...success });

  await page.getByRole('button', { name: '实时', exact: true }).click();
  await page.getByRole('button', { name: '开始任务' }).click();
  await page.locator('#requestMeta').getByText('POST /api/tasks · 403').waitFor({ timeout: 12000 });
  assert.match(await page.locator('#toastMessage').textContent(), /只允许预览/);
  assert.equal(await page.locator('#overviewStatus').textContent(), '任务未被接收');
  assert.equal(await page.locator('#safetyMetric').textContent(), '未执行');
  assert.equal(await page.locator('.timeline-item.active').count(), 0);
  assert.match(await page.locator('#logList').textContent(), /暂无运行记录/);
  await screenshot(page, '02_live_rejection_1280');
  results.cases.push({ id: 'live_rejection', type: 'browser E2E / safety', result: 'passed',
    trigger: 'click live and start', backend_response: 403,
    ui: await page.locator('#toastMessage').textContent() });
  await page.close();

  const imagePage = await newPage();
  // Complete a real preview first; only the later screenshot re-request is faulted.
  const imageTask = await submitPreview(imagePage);
  let imageFaultCount = 0;
  await imagePage.route(`**/api/tasks/${imageTask.task_id}/screenshot?**`, async route => {
    imageFaultCount++;
    await route.fulfill({ status: 404, contentType: 'application/json',
      body: JSON.stringify({ ok: false, error: 'injected_screenshot_failure' }) });
  });
  await imagePage.evaluate(() => pollTask());
  await imagePage.locator('#captureNote').getByText('截图加载失败').waitFor({ timeout: 12000 });
  assert(imageFaultCount > 0);
  assert(await imagePage.locator('#toast').evaluate(node => node.classList.contains('error')));
  await screenshot(imagePage, '03_screenshot_failure_1280');
  results.cases.push({ id: 'screenshot_failure', type: 'browser network fault / image response 404',
    result: 'passed', task_id: imageTask.task_id, injected_requests: imageFaultCount,
    ui: await imagePage.locator('#captureNote').textContent() });
  await imagePage.unrouteAll({ behavior: 'ignoreErrors' });
  await imagePage.evaluate(() => pollTask());
  await imagePage.locator('#captureNote').getByText('截图已加载').waitFor({ timeout: 12000 });
  results.cases.push({ id: 'screenshot_recovery', type: 'browser E2E / recovery', result: 'passed',
    ui: await imagePage.locator('#captureNote').textContent() });
  await imagePage.close();

  const timeoutPage = await newPage();
  let slowPost = 0;
  await timeoutPage.route('**/api/tasks', async route => {
    if (route.request().method() !== 'POST') return route.continue();
    slowPost++;
    await delay(9000);
    try { await route.abort('timedout'); } catch { /* browser aborted at eight seconds */ }
  });
  await timeoutPage.getByLabel('任务内容').fill('搜索 GUI Agent');
  await timeoutPage.getByRole('button', { name: '开始任务' }).click();
  await timeoutPage.locator('#requestMeta').getByText('POST /api/tasks · 超时').waitFor({ timeout: 14000 });
  assert.equal(await timeoutPage.locator('#toastMessage').textContent(), '本地执行器响应超时');
  assert(slowPost > 0);
  assert.equal(await timeoutPage.locator('#overviewStatus').textContent(), '请求超时');
  assert.equal(await timeoutPage.locator('#safetyMetric').textContent(), '未执行');
  assert.equal(await timeoutPage.locator('.timeline-item.active').count(), 0);
  assert.match(await timeoutPage.locator('#connectionState').textContent(), /已连接/);
  await screenshot(timeoutPage, '04_request_timeout_1280');
  results.cases.push({ id: 'request_timeout', type: 'browser network fault / POST delayed past 8000 ms',
    result: 'passed', injected_requests: slowPost,
    ui: await timeoutPage.locator('#requestMeta').textContent() });
  await timeoutPage.unrouteAll({ behavior: 'ignoreErrors' });
  const timeoutRecovery = await submitPreview(timeoutPage);
  results.cases.push({ id: 'timeout_recovery', type: 'browser E2E / retry after timeout', result: 'passed',
    task_id: timeoutRecovery.task_id });
  await timeoutPage.close();

  for (const width of [320, 375, 680, 768, 980, 1280]) {
    const viewportPage = await newPage(width);
    const measurement = await viewportPage.evaluate(() => {
      const ids = ['taskForm', 'screenPreview', 'runNote', 'requestMeta'];
      return { viewport: window.innerWidth, document: document.documentElement.scrollWidth,
        body: document.body.scrollWidth,
        panel_widths: [...document.querySelectorAll('.dashboard > .column')].map(node => node.getBoundingClientRect().width),
        controls: ids.map(id => {
          const rect = document.getElementById(id).getBoundingClientRect();
          return { id, left: rect.left, right: rect.right, width: rect.width };
        }) };
    });
    assert(measurement.document <= width + 1, `horizontal overflow at ${width}: ${measurement.document}`);
    assert(measurement.body <= width + 1, `body overflow at ${width}: ${measurement.body}`);
    for (const control of measurement.controls) {
      assert(control.left >= -1 && control.right <= width + 1, `${width} ${control.id} outside viewport`);
    }
    if (width <= 680) {
      assert(measurement.panel_widths.every(value => value >= width - 34),
        `${width} mobile cards do not fill workspace: ${measurement.panel_widths}`);
    }
    if (width === 320 || width === 375 || width === 768 || width === 1280) {
      await screenshot(viewportPage, `width_${width}`);
    }
    if (width === 320) {
      await viewportPage.getByLabel('任务内容').fill('搜索 GUI Agent');
      await viewportPage.getByRole('button', { name: '开始任务' }).click();
      await viewportPage.locator('#livePill').getByText('预览完成').waitFor({ timeout: 120000 });
      measurement.task_id = await viewportPage.locator('#requestMeta').textContent()
        .then(value => value.match(/任务 ([a-f0-9]{12})/)?.[1]);
      assert.match(measurement.task_id ?? '', /^[a-f0-9]{12}$/);
      await screenshot(viewportPage, 'width_320_preview_result');
    }
    results.widths.push(measurement);
    await viewportPage.close();
  }

  const offlinePage = await newPage();
  await stopBackend();
  await offlinePage.getByLabel('任务内容').fill('搜索 GUI Agent');
  await offlinePage.getByRole('button', { name: '开始任务' }).click();
  await offlinePage.locator('#requestMeta').getByText('POST /api/tasks · 网络错误').waitFor({ timeout: 12000 });
  assert.match(await offlinePage.locator('#connectionState').textContent(), /未连接/);
  assert.equal(await offlinePage.locator('#overviewStatus').textContent(), '本地执行器未连接');
  assert.equal(await offlinePage.locator('#toastMessage').textContent(), '本地执行器不可达');
  assert.equal(await offlinePage.locator('.timeline-item.active').count(), 0);
  assert.equal(await offlinePage.locator('#safetyMetric').textContent(), '未执行');
  await screenshot(offlinePage, '05_service_disconnected_1280');
  results.cases.push({ id: 'service_disconnected', type: 'browser E2E / actual service shutdown',
    result: 'passed', ui: await offlinePage.locator('#requestMeta').textContent() });
  await offlinePage.close();
  startBackend();
  await waitForHealth();
  const recoveryPage = await newPage();
  assert.match(await recoveryPage.locator('#connectionState').textContent(), /已连接/);
  const serviceRecovery = await submitPreview(recoveryPage);
  results.cases.push({ id: 'service_recovered', type: 'browser E2E / service restart', result: 'passed',
    ui: await recoveryPage.locator('#connectionState').textContent(), task_id: serviceRecovery.task_id });
  await recoveryPage.close();

  results.result = 'passed';
} catch (error) {
  results.result = 'failed';
  results.error = error.stack || String(error);
  console.error(results.error);
  process.exitCode = 1;
} finally {
  if (browser) await browser.close();
  await stopBackend();
  await writeFile(resolve(output, 'backend.log'), backendLog);
  await writeFile(resolve(output, 'results.json'), JSON.stringify(results, null, 2) + '\n');
  console.log(resolve(output, 'results.json'));
}

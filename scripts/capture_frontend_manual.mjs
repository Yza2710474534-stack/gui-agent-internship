import { chromium } from '/Users/ziang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import { mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';

const project = resolve(import.meta.dirname, '..');
const output = resolve(project, 'output/frontend_manual/screenshots');
const frontend = `file://${resolve(project, 'gui-agent-console/dist/index.html')}`;
await mkdir(output, { recursive: true });

const browser = await chromium.launch({
  headless: true,
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  args: ['--no-first-run', '--no-default-browser-check'],
});
const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });

let online = false;
await page.route('http://127.0.0.1:8765/**', async (route) => {
  const path = new URL(route.request().url()).pathname;
  if (!online) return route.abort('failed');
  if (path === '/api/health') {
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      headers: { 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({ ok: true, service: 'GUI Agent Local Executor', live_enabled: false }),
    });
  }
  return route.fulfill({
    status: 404,
    contentType: 'application/json',
    headers: { 'Access-Control-Allow-Origin': '*' },
    body: JSON.stringify({ ok: false, error: 'fixture_only' }),
  });
});

async function screenshot(name) {
  await page.screenshot({ path: resolve(output, name), fullPage: true });
}

function task(status, step, overrides = {}) {
  const labels = {
    queued: [],
    observing: [
      { time: '10:24:01', message: '任务已由本地执行器接收', status: '已接收' },
      { time: '10:24:03', message: '正在加载 OCR 并读取当前屏幕', status: '进行中' },
    ],
    planning: [
      { time: '10:24:01', message: '任务已由本地执行器接收', status: '已接收' },
      { time: '10:24:09', message: '屏幕识别完成，共发现 18 个文字区域', status: '完成' },
      { time: '10:24:10', message: '已定位“编辑”，坐标 (176, 12)', status: '完成' },
    ],
    preview_ready: [
      { time: '10:24:01', message: '任务已由本地执行器接收', status: '已接收' },
      { time: '10:24:09', message: '屏幕识别完成，共发现 18 个文字区域', status: '完成' },
      { time: '10:24:10', message: '已定位“编辑”，坐标 (176, 12)', status: '完成' },
      { time: '10:24:10', message: '动作方案已生成', status: '完成' },
    ],
    paused: [
      { time: '10:24:01', message: '任务已由本地执行器接收', status: '已接收' },
      { time: '10:24:05', message: '任务已暂停', status: '暂停' },
    ],
    failed: [
      { time: '10:24:01', message: '任务已由本地执行器接收', status: '已接收' },
      { time: '10:24:02', message: '本地执行器看不到屏幕，请检查屏幕录制权限', status: '失败' },
    ],
  };
  return {
    id: 'manualfixture',
    task: '点击“编辑”',
    mode: 'preview',
    status,
    step,
    logs: labels[status] || [],
    metrics: { ocr_items: status === 'planning' || status === 'preview_ready' ? 18 : null,
      confidence: status === 'planning' || status === 'preview_ready' ? 94.2 : null,
      safety: status === 'failed' ? '未通过' : status === 'preview_ready' ? '通过' : '检查中' },
    result: status === 'preview_ready' ? { proposed_action: { type: 'click', x: 176, y: 12 } } : null,
    error: status === 'failed' ? '本地执行器看不到屏幕，请从已获得屏幕录制权限的终端启动' : null,
    screenshot_url: null,
    ...overrides,
  };
}

await page.goto(frontend);
await page.waitForTimeout(2500);
await screenshot('01_connection_offline.png');

online = true;
await page.reload();
await page.getByText('本地执行器已连接 · 仅预览').waitFor();
await screenshot('02_connected_idle.png');

await page.getByLabel('任务内容').fill('点击“编辑”');
await screenshot('03_task_configured.png');

for (const [name, fixture] of [
  ['04_observing.png', task('observing', 2)],
  ['05_planning.png', task('planning', 3)],
  ['06_preview_result.png', task('preview_ready', 4)],
  ['07_paused.png', task('paused', 2)],
  ['08_permission_error.png', task('failed', 4)],
]) {
  await page.evaluate((value) => renderTask(value), fixture);
  await screenshot(name);
}

await browser.close();
console.log(output);

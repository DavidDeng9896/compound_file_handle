const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const AI_DEFAULTS = require('./ai_defaults');

const PROJECT_ROOT = path.join(__dirname, '..');

function pythonExecutable() {
  if (process.env.PYTHON) return process.env.PYTHON;
  return process.platform === 'win32' ? 'python' : 'python3';
}

/** 打包后使用 PyInstaller 生成的 cdxml-bridge；开发时使用 python -m cdxml.bridge */
function getBridgeSpawnConfig(cdxmlPath, outputPath, matchOptions) {
  const xl =
    matchOptions && typeof matchOptions.matchXExtendLeft === 'number'
      ? String(matchOptions.matchXExtendLeft)
      : '0';
  const xr =
    matchOptions && typeof matchOptions.matchXExtendRight === 'number'
      ? String(matchOptions.matchXExtendRight)
      : '0';
  const yd =
    matchOptions && typeof matchOptions.matchYDown === 'number'
      ? String(matchOptions.matchYDown)
      : '130';
  if (app.isPackaged) {
    const bridgeDir = path.join(process.resourcesPath, 'bridge');
    const exeName = process.platform === 'win32' ? 'cdxml-bridge.exe' : 'cdxml-bridge';
    const bridgeExe = path.join(bridgeDir, exeName);
    return {
      cmd: bridgeExe,
      args: [cdxmlPath, outputPath, xl, xr, yd],
      cwd: bridgeDir,
    };
  }
  return {
    cmd: pythonExecutable(),
    args: [
      '-m',
      'cdxml.bridge',
      cdxmlPath,
      outputPath,
      xl,
      xr,
      yd,
    ],
    cwd: PROJECT_ROOT,
  };
}

function runBridge(cdxmlPath, outputPath, matchOptions) {
  return new Promise((resolve, reject) => {
    const { cmd, args, cwd } = getBridgeSpawnConfig(cdxmlPath, outputPath, matchOptions);
    if (app.isPackaged && !fs.existsSync(cmd)) {
      reject(
        new Error(
          `未找到解析核心：${cmd}\n请使用官方安装包重新安装，或联系发布方。`
        )
      );
      return;
    }
    const child = spawn(cmd, args, {
      cwd,
      windowsHide: true,
      env: {
        ...process.env,
        PYTHONUTF8: '1',
        PYTHONIOENCODING: 'utf-8',
      },
    });
    let stderr = '';
    let stdout = '';
    child.stdout.on('data', (d) => {
      stdout += d.toString('utf8');
    });
    child.stderr.on('data', (d) => {
      stderr += d.toString('utf8');
    });
    child.on('error', (err) => {
      const hint = app.isPackaged
        ? '解析核心无法启动，请重新安装应用。'
        : `无法启动 ${cmd}：${err.message}。开发环境请安装 Python、rdkit，并将 python 加入 PATH，或设置环境变量 PYTHON。`;
      reject(new Error(hint));
    });
    child.on('close', () => {
      const trimmed = stdout.trim();
      if (!trimmed) {
        reject(new Error(stderr || '未收到解析结果（stdout 为空）'));
        return;
      }
      const lastLine = trimmed.includes('\n') ? trimmed.split('\n').pop() : trimmed;
      try {
        const payload = JSON.parse(lastLine);
        if (stderr) payload._stderr_extra = stderr;
        resolve(payload);
      } catch (e) {
        reject(new Error(`解析 JSON 失败：${e.message}\n--- stdout ---\n${stdout}\n--- stderr ---\n${stderr}`));
      }
    });
  });
}

function aiConfigPath() {
  return path.join(app.getPath('userData'), 'ai_config.json');
}

function loadAiConfigFromDisk() {
  const merged = { ...AI_DEFAULTS };
  try {
    const p = aiConfigPath();
    if (fs.existsSync(p)) {
      const saved = JSON.parse(fs.readFileSync(p, 'utf8'));
      Object.assign(merged, saved);
    }
  } catch (_) {
    /* use defaults */
  }
  return merged;
}

function saveAiConfigToDisk(config) {
  const toSave = { ...config };
  const dir = app.getPath('userData');
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(aiConfigPath(), JSON.stringify(toSave, null, 2), 'utf8');
}

function getTextAiBridgeSpawnConfig() {
  if (app.isPackaged) {
    const bridgeDir = path.join(process.resourcesPath, 'text-ai-bridge');
    const exeName = process.platform === 'win32' ? 'text-ai-bridge.exe' : 'text-ai-bridge';
    const bridgeExe = path.join(bridgeDir, exeName);
    return { cmd: bridgeExe, args: [], cwd: bridgeDir };
  }
  return {
    cmd: pythonExecutable(),
    args: ['-m', 'cdxml.text_ai_bridge'],
    cwd: PROJECT_ROOT,
  };
}

/** @type {{ child: import('child_process').ChildProcess, superseded: boolean, mode: string } | null} */
let textAiJob = null;

function killTextAiChild(child) {
  if (!child || child.killed) return;
  try {
    if (process.platform === 'win32' && child.pid) {
      spawn('taskkill', ['/pid', String(child.pid), '/T', '/F'], { windowsHide: true });
    } else {
      child.kill('SIGTERM');
    }
  } catch (_) {
    try {
      child.kill();
    } catch (__) {
      /* ignore */
    }
  }
}

/**
 * 取消当前 AI batch 子进程。返回是否确实取消了任务。
 * @param {Electron.WebContents | null} sender
 * @param {{ notify?: boolean }} [opts]
 */
function cancelTextAiJob(sender, opts = {}) {
  const notify = opts.notify !== false;
  return new Promise((resolve) => {
    const job = textAiJob;
    if (!job || !job.child) {
      resolve(false);
      return;
    }
    job.superseded = true;
    textAiJob = null;
    let settled = false;
    const finish = () => {
      if (settled) return;
      settled = true;
      if (notify && sender && !sender.isDestroyed()) {
        sender.send('ai-progress', {
          type: 'cancelled',
          message: '已取消上一批 AI 任务',
        });
      }
      resolve(true);
    };
    job.child.once('close', finish);
    job.child.once('exit', finish);
    killTextAiChild(job.child);
    setTimeout(finish, 2500);
  });
}

function parseProgressLines(chunk, bufRef, onProgress) {
  bufRef.value += chunk;
  const parts = bufRef.value.split(/\r?\n/);
  bufRef.value = parts.pop() || '';
  for (const line of parts) {
    const t = line.trim();
    if (!t.startsWith('{')) continue;
    try {
      const obj = JSON.parse(t);
      if (obj && obj.type === 'progress') onProgress(obj);
    } catch (_) {
      /* 非进度 JSON，忽略 */
    }
  }
}

function runTextAiBridge(webContents, stdinPayload, mode) {
  return new Promise((resolve, reject) => {
    const { cmd, args, cwd } = getTextAiBridgeSpawnConfig();
    const spawnArgs = mode === 'test' ? [...args, '--test'] : args;
    if (app.isPackaged && !fs.existsSync(cmd)) {
      reject(new Error(`未找到 AI 结构化核心：${cmd}\n请使用含 text-ai-bridge 的安装包重新构建。`));
      return;
    }
    const child = spawn(cmd, spawnArgs, {
      cwd,
      windowsHide: true,
      env: {
        ...process.env,
        PYTHONUTF8: '1',
        PYTHONIOENCODING: 'utf-8',
        CDXML_AI_CACHE_DIR: path.join(app.getPath('userData'), 'text_ai_cache'),
      },
    });

    const job = { child, superseded: false, mode };
    if (mode === 'batch') {
      textAiJob = job;
    }

    let stderr = '';
    let stdout = '';
    const stderrBuf = { value: '' };

    child.stdout.on('data', (d) => {
      stdout += d.toString('utf8');
    });
    child.stderr.on('data', (d) => {
      const chunk = d.toString('utf8');
      stderr += chunk;
      if (mode === 'batch') {
        parseProgressLines(chunk, stderrBuf, (obj) => {
          if (job.superseded) return;
          if (webContents && !webContents.isDestroyed()) {
            webContents.send('ai-progress', obj);
          }
        });
      }
    });
    child.on('error', (err) => {
      if (textAiJob === job) textAiJob = null;
      if (job.superseded) {
        resolve({ success: false, cancelled: true, message: '已取消上一批 AI 任务' });
        return;
      }
      const hint = app.isPackaged
        ? 'AI 结构化核心无法启动，请重新安装应用。'
        : `无法启动 ${cmd}：${err.message}`;
      reject(new Error(hint));
    });
    child.on('close', () => {
      if (textAiJob === job) textAiJob = null;
      if (job.superseded) {
        resolve({ success: false, cancelled: true, message: '已取消上一批 AI 任务' });
        return;
      }
      const trimmed = stdout.trim();
      if (!trimmed) {
        reject(new Error(stderr || '未收到 AI 结构化结果（stdout 为空）'));
        return;
      }
      const lastLine = trimmed.includes('\n') ? trimmed.split('\n').pop() : trimmed;
      try {
        const payload = JSON.parse(lastLine);
        if (stderr) payload._stderr_extra = stderr;
        resolve(payload);
      } catch (e) {
        reject(new Error(`解析 JSON 失败：${e.message}\n--- stdout ---\n${stdout}`));
      }
    });
    const body = mode === 'test' ? { config: stdinPayload.config || stdinPayload } : stdinPayload;
    child.stdin.write(JSON.stringify(body), 'utf8');
    child.stdin.end();
  });
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1120,
    height: 780,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });
  win.loadFile(path.join(__dirname, 'index.html'));
}

app.whenReady().then(() => {
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

ipcMain.handle('parse', async (_evt, cdxmlPath, outputPath, matchOptions) => {
  return runBridge(cdxmlPath, outputPath, matchOptions);
});

ipcMain.handle('ai-config-load', async () => {
  const cfg = loadAiConfigFromDisk();
  return {
    ...cfg,
    api_key_set: Boolean((cfg.api_key || '').trim() || process.env.CDXML_AI_API_KEY),
  };
});

ipcMain.handle('ai-config-save', async (_evt, config) => {
  if (!config || typeof config !== 'object') {
    throw new Error('无效配置');
  }
  saveAiConfigToDisk(config);
  return true;
});

ipcMain.handle('ai-test-connection', async (evt, configFromUi) => {
  const disk = loadAiConfigFromDisk();
  const config = { ...disk, ...configFromUi };
  if (configFromUi && !configFromUi.api_key && disk.api_key) {
    config.api_key = disk.api_key;
  }
  return runTextAiBridge(evt.sender, { config }, 'test');
});

ipcMain.handle('cancel-text-ai', async (evt) => {
  const cancelled = await cancelTextAiJob(evt.sender, { notify: true });
  return { cancelled };
});

ipcMain.handle('parse-text-ai', async (evt, compounds, configFromUi) => {
  await cancelTextAiJob(evt.sender, { notify: false });
  const disk = loadAiConfigFromDisk();
  const config = { ...disk, ...configFromUi };
  if (configFromUi && !configFromUi.api_key && disk.api_key) {
    config.api_key = disk.api_key;
  }
  config.cache_dir = path.join(app.getPath('userData'), 'text_ai_cache');
  const list = (compounds || []).map((c) => ({
    compound_id: c.compound_id || c.name || '',
    text: c.text || '',
  }));
  return runTextAiBridge(evt.sender, { config, compounds: list }, 'batch');
});

ipcMain.handle('dialog-pick-dir', async (event) => {
  const win = BrowserWindow.fromWebContents(event.sender);
  const r = await dialog.showOpenDialog(win, {
    title: '选择导出目录',
    properties: ['openDirectory', 'createDirectory'],
  });
  if (r.canceled || !r.filePaths[0]) return null;
  return r.filePaths[0];
});

ipcMain.handle('write-files', async (_evt, fileMap) => {
  const fsp = require('fs/promises');
  for (const [filePath, content] of Object.entries(fileMap || {})) {
    await fsp.writeFile(filePath, content, { encoding: 'utf8' });
  }
  return true;
});

ipcMain.handle('dialog-open-cdxml', async (event) => {
  const win = BrowserWindow.fromWebContents(event.sender);
  const r = await dialog.showOpenDialog(win, {
    title: '选择 CDXML 文件',
    filters: [{ name: 'ChemDraw XML', extensions: ['cdxml'] }, { name: '所有文件', extensions: ['*'] }],
    properties: ['openFile'],
  });
  if (r.canceled || !r.filePaths[0]) return null;
  return r.filePaths[0];
});

ipcMain.handle('dialog-save-csv', async (event, defaultName) => {
  const win = BrowserWindow.fromWebContents(event.sender);
  const r = await dialog.showSaveDialog(win, {
    title: '保存解析结果 CSV',
    defaultPath: defaultName || 'compounds_output.csv',
    filters: [{ name: 'CSV', extensions: ['csv'] }],
  });
  if (r.canceled || !r.filePath) return null;
  return r.filePath;
});

ipcMain.handle('dialog-save-review', async (event, defaultName) => {
  const win = BrowserWindow.fromWebContents(event.sender);
  const r = await dialog.showSaveDialog(win, {
    title: '导出审查清单 CSV',
    defaultPath: defaultName || 'review_unmatched.csv',
    filters: [{ name: 'CSV', extensions: ['csv'] }],
  });
  if (r.canceled || !r.filePath) return null;
  return r.filePath;
});

ipcMain.handle('write-file', async (_evt, filePath, content) => {
  const fs = require('fs/promises');
  await fs.writeFile(filePath, content, { encoding: 'utf8' });
  return true;
});

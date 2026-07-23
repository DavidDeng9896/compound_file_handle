const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('cdxmlApi', {
  parse: (cdxmlPath, outputPath, matchOptions) =>
    ipcRenderer.invoke('parse', cdxmlPath, outputPath, matchOptions),
  dialogOpenCdxml: () => ipcRenderer.invoke('dialog-open-cdxml'),
  dialogSaveCsv: (defaultName) => ipcRenderer.invoke('dialog-save-csv', defaultName),
  dialogSaveReview: (defaultName) => ipcRenderer.invoke('dialog-save-review', defaultName),
  dialogPickDir: () => ipcRenderer.invoke('dialog-pick-dir'),
  writeFile: (filePath, content) => ipcRenderer.invoke('write-file', filePath, content),
  writeFiles: (fileMap) => ipcRenderer.invoke('write-files', fileMap),
  aiConfigLoad: () => ipcRenderer.invoke('ai-config-load'),
  aiConfigSave: (cfg) => ipcRenderer.invoke('ai-config-save', cfg),
  aiTestConnection: (cfg) => ipcRenderer.invoke('ai-test-connection', cfg),
  parseTextAi: (compounds, cfg) => ipcRenderer.invoke('parse-text-ai', compounds, cfg),
  cancelTextAi: () => ipcRenderer.invoke('cancel-text-ai'),
  onAiProgress: (callback) => {
    const handler = (_evt, data) => callback(data);
    ipcRenderer.on('ai-progress', handler);
    return () => ipcRenderer.removeListener('ai-progress', handler);
  },
});

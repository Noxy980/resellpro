const { app, BrowserWindow, shell } = require('electron')
const { spawn } = require('child_process')
const path = require('path')
const fs = require('fs')

let mainWindow
let backendProcess

function getBackendDir() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'backend')
  }
  return path.join(__dirname, '..', '..', 'backend')
}

function getProjectRoot() {
  if (app.isPackaged) {
    return process.resourcesPath
  }
  return path.join(__dirname, '..', '..')
}

function startBackend() {
  const backendDir = getBackendDir()
  const projectRoot = getProjectRoot()
  const pythonCmd = process.platform === 'win32' ? 'python' : 'python3'

  const env = {
    ...process.env,
    RESELLPRO_ROOT: projectRoot,
    PYTHONPATH: projectRoot,
  }

  backendProcess = spawn(pythonCmd, ['run.py'], {
    cwd: backendDir,
    stdio: 'pipe',
    env,
  })

  backendProcess.stdout.on('data', d => console.log('[backend]', d.toString()))
  backendProcess.stderr.on('data', d => console.error('[backend]', d.toString()))
  backendProcess.on('error', err => console.error('[backend] spawn error:', err))
}

function createWindow() {
  const iconPath = path.join(__dirname, '..', 'build', 'icon.png')
  mainWindow = new BrowserWindow({
    width: 1360,
    height: 860,
    minWidth: 1024,
    minHeight: 640,
    title: 'ResellPro',
    backgroundColor: '#f8f9fc',
    icon: fs.existsSync(iconPath) ? iconPath : undefined,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
    autoHideMenuBar: true,
    show: false,
  })

  mainWindow.once('ready-to-show', () => mainWindow.show())

  const isDev = !app.isPackaged
  if (isDev) {
    mainWindow.loadURL('http://localhost:5173')
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'))
  }

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url)
    return { action: 'deny' }
  })
}

app.whenReady().then(() => {
  startBackend()
  setTimeout(createWindow, 2500)
})

app.on('window-all-closed', () => {
  if (backendProcess) backendProcess.kill()
  if (process.platform !== 'darwin') app.quit()
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow()
})

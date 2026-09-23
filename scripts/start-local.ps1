param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$backendRoot = Join-Path $projectRoot 'backend'
$frontendRoot = Join-Path $projectRoot 'frontend'
$logRoot = Join-Path $projectRoot '.local'
New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
$pythonExe = Join-Path $backendRoot '.venv\Scripts\python.exe'

function Invoke-Checked {
    param([string]$Program, [string[]]$Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Falha ao executar $Program. Confira a mensagem acima." }
}
function Test-LocalUrl {
    param([string]$Url)
    try { return (Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200 } catch { return $false }
}

try {
    $nodeExe = (Get-Command node.exe -ErrorAction Stop).Source
    $npmExe = (Get-Command npm.cmd -ErrorAction Stop).Source
    if (!(Test-Path -LiteralPath $pythonExe)) {
        $pythonCommand = Get-Command py.exe -ErrorAction SilentlyContinue
        if (!$pythonCommand) { $pythonCommand = Get-Command python.exe -ErrorAction Stop }
        Invoke-Checked $pythonCommand.Source @('-m', 'venv', (Join-Path $backendRoot '.venv'))
    }
    Push-Location $backendRoot
    try {
        Invoke-Checked $pythonExe @('-m', 'pip', 'install', '-r', 'requirements.txt')
        Invoke-Checked $pythonExe @('manage.py', 'migrate', '--noinput')
    } finally { Pop-Location }
    Push-Location $frontendRoot
    try {
        $lockHash = (Get-FileHash -LiteralPath 'package-lock.json').Hash
        $hashFile = Join-Path $logRoot 'frontend-dependencies.sha256'
        $previousHash = if (Test-Path -LiteralPath $hashFile) { (Get-Content -LiteralPath $hashFile -Raw).Trim() } else { '' }
        if (!(Test-Path -LiteralPath 'node_modules/vite/bin/vite.js') -or $lockHash -ne $previousHash) {
            Invoke-Checked $npmExe @('install')
            (Get-FileHash -LiteralPath 'package-lock.json').Hash | Set-Content -LiteralPath $hashFile
        }
    } finally { Pop-Location }

    if (!(Test-LocalUrl 'http://127.0.0.1:8000/api/spaces/')) {
        $server = Start-Process -FilePath $pythonExe -ArgumentList '-u manage.py runserver 127.0.0.1:8000 --noreload' -WorkingDirectory $backendRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logRoot 'backend.log') -RedirectStandardError (Join-Path $logRoot 'backend-error.log')
        $server.Id | Set-Content (Join-Path $logRoot 'backend.pid')
    }
    if (!(Test-LocalUrl 'http://localhost:5173/')) {
        $web = Start-Process -FilePath $nodeExe -ArgumentList 'node_modules/vite/bin/vite.js --host localhost --port 5173 --strictPort' -WorkingDirectory $frontendRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logRoot 'frontend.log') -RedirectStandardError (Join-Path $logRoot 'frontend-error.log')
        $web.Id | Set-Content (Join-Path $logRoot 'frontend.pid')
    }
    $ready = $false
    for ($attempt = 0; $attempt -lt 20; $attempt++) {
        if ((Test-LocalUrl 'http://127.0.0.1:8000/api/spaces/') -and (Test-LocalUrl 'http://localhost:5173/')) { $ready = $true; break }
        Start-Sleep -Milliseconds 500
    }
    if (!$ready) { throw "Os servidores não iniciaram. Consulte os arquivos em $logRoot." }
    Write-Host 'Garage Rent disponível em http://localhost:5173/'
    Write-Host "Logs e links de verificação de e-mail: $logRoot"
    if (!$NoBrowser) { Start-Process 'http://localhost:5173/' }
} catch {
    Write-Host "Não foi possível abrir o site: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host 'Confira se Python e Node.js estão instalados e se as portas 8000 e 5173 estão livres.'
    exit 1
}

param(
  [Parameter(Mandatory = $true, Position = 0)]
  [string]$Text,

  [string]$Config,

  [string]$Python = "python",

  [switch]$NoPlay
)

$ErrorActionPreference = "Stop"
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $repoRoot) {
  $repoRoot = (Get-Location).Path
}
$repoRoot = (Resolve-Path -LiteralPath $repoRoot).Path

if (-not $Config -or [string]::IsNullOrWhiteSpace($Config)) {
  $localConfig = Join-Path $repoRoot "config.json"
  if (Test-Path -LiteralPath $localConfig) {
    $Config = $localConfig
  }
  else {
    $Config = Join-Path $repoRoot "config.example.json"
  }
}

if (-not [System.IO.Path]::IsPathRooted($Config)) {
  $Config = Join-Path $repoRoot $Config
}
$Config = (Resolve-Path -LiteralPath $Config).Path

$speakPy = Join-Path $repoRoot "scripts\speak.py"
if (-not (Test-Path -LiteralPath $speakPy)) {
  throw "Cannot find scripts/speak.py at: $speakPy"
}

$argsList = @($speakPy, $Text, "--config", $Config)
if ($NoPlay) {
  $argsList += "--no-play"
}

& $Python @argsList
$exitCode = $LASTEXITCODE
if ($exitCode -ne 0) {
  exit $exitCode
}

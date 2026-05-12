param(
    [Parameter(Mandatory = $true)]
    [string]$UrlOrPath,

    [string]$Out = "tmp/playwright-chrome-smoke.png",
    [string]$Viewport = "1440,900",
    [int]$WaitForTimeout = 200
)

$ErrorActionPreference = "Stop"

$npx = Get-Command npx.cmd -ErrorAction SilentlyContinue
if (-not $npx) {
    $npx = Get-Command npx -ErrorAction SilentlyContinue
}
if (-not $npx) {
    throw "npx was not found. Install Node.js/npm, then retry."
}

$chromeCandidates = @(
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe",
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe"
)
$chromePath = $chromeCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $chromePath) {
    throw "Google Chrome was not found. Install Chrome or change this script to another Playwright channel."
}

if (Test-Path -LiteralPath $UrlOrPath) {
    $target = ([System.Uri]::new((Resolve-Path -LiteralPath $UrlOrPath).Path)).AbsoluteUri
}
else {
    $target = $UrlOrPath
}

$outParent = Split-Path -Parent $Out
if ($outParent) {
    New-Item -ItemType Directory -Force -Path $outParent | Out-Null
}

$argsList = @(
    "playwright",
    "screenshot",
    "--channel",
    "chrome",
    "--viewport-size=$Viewport"
)
if ($WaitForTimeout -gt 0) {
    $argsList += @("--wait-for-timeout", [string]$WaitForTimeout)
}
$argsList += @($target, $Out)

Write-Host "chrome=$chromePath"
Write-Host "target=$target"
Write-Host "out=$Out"
& $npx.Source @argsList
if ($LASTEXITCODE -ne 0) {
    throw "Playwright screenshot failed with exit code $LASTEXITCODE"
}
Write-Host "saved=$Out"

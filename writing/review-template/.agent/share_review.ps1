# Prints the public link of the manuscript review page (Windows + cloudflared).
# Reuses a live Cloudflare tunnel if available, otherwise starts review_server.py and/or a new tunnel.
$port = if ($env:REVIEW_PORT) { $env:REVIEW_PORT } else { '8766' }
$page = 'manuscript.html'
$urlFile = Join-Path $env:TEMP "manuscript_tunnel_${port}_url.txt"
$log = Join-Path $env:TEMP "manuscript_tunnel_${port}.log"
$cf = (Get-Command cloudflared -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1)
if (-not $cf) { $cf = 'C:\Program Files (x86)\cloudflared\cloudflared.exe' }

function Up($u) {
    try { (Invoke-WebRequest "$u/$page" -Method Head -UseBasicParsing -TimeoutSec 5).StatusCode -eq 200 } catch { $false }
}

function Spawn($cmd) {
    $cfg = New-CimInstance -ClassName Win32_ProcessStartup -Property @{ ShowWindow = [uint16]0 } -ClientOnly
    $r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = $cmd; ProcessStartupInformation = $cfg }
    if ($r.ReturnValue -ne 0) { throw "Failed to start: $cmd (code $($r.ReturnValue))" }
}

if (-not (Up "http://127.0.0.1:$port")) {
    $py = (Get-Command python -ErrorAction Stop).Source
    Spawn "`"$py`" `"$PSScriptRoot\review_server.py`""
    for ($i = 0; $i -lt 10 -and -not (Up "http://127.0.0.1:$port"); $i++) { Start-Sleep 1 }
}

$url = if (Test-Path $urlFile) { (Get-Content $urlFile -Raw).Trim() }
if (-not ($url -and (Up $url))) {
    if (-not (Test-Path $cf)) { throw "cloudflared not found. Use local http://127.0.0.1:$port/$page or install cloudflared." }
    Remove-Item $log -ErrorAction SilentlyContinue
    Spawn "`"$cf`" tunnel --logfile `"$log`" --url http://127.0.0.1:$port"
    $url = $null
    for ($i = 0; $i -lt 30 -and -not $url; $i++) {
        Start-Sleep 1
        $m = Select-String -Path $log -Pattern 'https://[a-z0-9-]+\.trycloudflare\.com' -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($m) { $url = $m.Matches.Value }
    }
    if (-not $url) { throw "Timed out waiting for cloudflared tunnel URL. See $log" }
    for ($i = 0; $i -lt 20 -and -not (Up $url); $i++) { Start-Sleep 1 }
    Set-Content $urlFile $url
}
"$url/$page"

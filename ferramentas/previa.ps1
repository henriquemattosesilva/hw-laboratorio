# Captura o index.html pelo Chrome DevTools Protocol e reporta erros de console.
#
#   pwsh ferramentas/previa.ps1 -Largura 390 -Destino previa-390.png
#
# Nao usa "--headless --screenshot": no Windows o --window-size nao vale para o
# viewport e a captura sai com largura diferente da pedida. O
# Emulation.setDeviceMetricsOverride vale, e por isso a conferencia passa pelo
# protocolo em vez de pela linha de comando.
param(
  [int]$Largura = 390,
  [int]$Altura = 900,
  [string]$Destino = "previa.png",
  [string]$Arquivo = "index.html",
  [int]$Porta = 9222,
  # Expressao JS executada depois de carregar e antes de capturar. Serve para
  # conferir estado que so existe depois de interagir — clicar num filtro,
  # digitar na busca, abrir uma secao.
  [string]$Antes = "",
  # Sem isto captura so a dobra, que e o que se olha. Com 85 cartoes a pagina
  # inteira vira uma tira de dezenas de milhares de pixels, ilegivel no olho.
  [switch]$Inteira
)
$ErrorActionPreference = "Stop"

$raiz = Split-Path -Parent $PSScriptRoot
$alvo = "file:///" + ((Join-Path $raiz $Arquivo) -replace '\\', '/')
$perfil = Join-Path $env:TEMP ("cdp-" + [System.Guid]::NewGuid().ToString("N"))
$chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"
if (-not (Test-Path $chrome)) { throw "Chrome nao encontrado em $chrome" }

$proc = Start-Process $chrome -PassThru -ArgumentList @(
  "--remote-debugging-port=$Porta", "--user-data-dir=$perfil",
  "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
  "about:blank"
)

function Obter-Ws([int]$porta) {
  foreach ($i in 1..40) {
    try {
      $alvos = Invoke-RestMethod "http://127.0.0.1:$porta/json" -TimeoutSec 2
      $pagina = $alvos | Where-Object { $_.type -eq "page" } | Select-Object -First 1
      if ($pagina) { return $pagina.webSocketDebuggerUrl }
    } catch { }
    Start-Sleep -Milliseconds 250
  }
  throw "o Chrome nao abriu a porta de depuracao $porta"
}

$ws = New-Object System.Net.WebSockets.ClientWebSocket
$ws.ConnectAsync([Uri](Obter-Ws $Porta), [Threading.CancellationToken]::None).Wait()

$script:seq = 0
$script:erros = @()

function Enviar([string]$metodo, $params) {
  $script:seq++
  $corpo = @{ id = $script:seq; method = $metodo; params = $params } |
    ConvertTo-Json -Depth 10 -Compress
  $bytes = [Text.Encoding]::UTF8.GetBytes($corpo)
  $ws.SendAsync([ArraySegment[byte]]::new($bytes), 'Text', $true,
                [Threading.CancellationToken]::None).Wait()

  # Le ate chegar a resposta com o id pedido. Os eventos que chegam no meio nao
  # sao descartados: os de erro viram $script:erros.
  while ($true) {
    $buf = [ArraySegment[byte]]::new((New-Object byte[] 262144))
    $texto = ""
    do {
      $r = $ws.ReceiveAsync($buf, [Threading.CancellationToken]::None).GetAwaiter().GetResult()
      $texto += [Text.Encoding]::UTF8.GetString($buf.Array, 0, $r.Count)
    } while (-not $r.EndOfMessage)

    $msg = $texto | ConvertFrom-Json
    if ($msg.id -eq $script:seq) { return $msg.result }
    if ($msg.method -eq "Runtime.consoleAPICalled" -and $msg.params.type -eq "error") {
      $script:erros += (($msg.params.args | ForEach-Object { $_.value }) -join " ")
    }
    if ($msg.method -eq "Runtime.exceptionThrown") {
      $script:erros += $msg.params.exceptionDetails.text
    }
  }
}

Enviar "Runtime.enable" @{} | Out-Null
Enviar "Page.enable" @{} | Out-Null
Enviar "Emulation.setDeviceMetricsOverride" @{
  width = $Largura; height = $Altura; deviceScaleFactor = 2; mobile = ($Largura -lt 700)
} | Out-Null
Enviar "Page.navigate" @{ url = $alvo } | Out-Null
Start-Sleep -Milliseconds 1500

if ($Antes) {
  $r = Enviar "Runtime.evaluate" @{ expression = $Antes; returnByValue = $true }
  if ($r.exceptionDetails) { throw "erro no -Antes: $($r.exceptionDetails.text)" }
  Start-Sleep -Milliseconds 400
}

$medida = Enviar "Runtime.evaluate" @{
  expression = "JSON.stringify({larg: innerWidth, rolagem: document.documentElement.scrollWidth, pecas: document.querySelectorAll('.peca').length, secoes: document.querySelectorAll('section').length})"
  returnByValue = $true
}
$m = $medida.result.value | ConvertFrom-Json

$tiro = Enviar "Page.captureScreenshot" @{
  format = "png"; captureBeyondViewport = [bool]$Inteira
}
$destAbs = if ([IO.Path]::IsPathRooted($Destino)) { $Destino }
           else { Join-Path (Get-Location) $Destino }
[IO.File]::WriteAllBytes($destAbs, [Convert]::FromBase64String($tiro.data))

Write-Output "viewport: $($m.larg) px | scrollWidth: $($m.rolagem) px | cartoes: $($m.pecas) | secoes: $($m.secoes)"
if ($m.rolagem -gt $m.larg) { Write-Output "FALHA: a pagina estoura horizontalmente" }
if ($script:erros.Count) {
  Write-Output "FALHA: $($script:erros.Count) erro(s) de console:"
  $script:erros | ForEach-Object { Write-Output "  $_" }
} else {
  Write-Output "console limpo"
}
Write-Output "$destAbs gerado"

$ws.Dispose()
Stop-Process -Id $proc.Id -Force
Remove-Item $perfil -Recurse -Force -ErrorAction SilentlyContinue

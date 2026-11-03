$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$taskTex = Join-Path $taskRoot 'output/pdf/lab9_prelab_postlab.tex'
$taskOutput = Join-Path $taskRoot 'output/pdf'
$taskBuild = Join-Path $taskRoot 'tmp/latex-build'
New-Item -ItemType Directory -Path $taskBuild -Force | Out-Null
for ($taskPass = 1; $taskPass -le 3; $taskPass++) {
    & xelatex '-interaction=nonstopmode' '-halt-on-error' "-output-directory=$taskBuild" $taskTex
    if ($LASTEXITCODE -ne 0) {
        throw "XeLaTeX failed on pass $taskPass. See $taskBuild"
    }
}
Copy-Item -LiteralPath (Join-Path $taskBuild 'lab9_prelab_postlab.pdf') -Destination $taskOutput -Force
Write-Host "PDF ready: $(Join-Path $taskOutput 'lab9_prelab_postlab.pdf')"

# One-shot training session: opponent-pool training on GPU, then automatic evaluation.
# Run from anywhere:  powershell -ExecutionPolicy Bypass -File scripts\run_pool_training.ps1
# Total wall-clock: ~80 min training (auto-stops on time budget) + ~5 min evaluation.

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo
$env:PYTHONUNBUFFERED = "1"

$exe = Join-Path $repo ".venv\Scripts\animal-shogi-lab.exe"
$frozen = "checkpoints/animal_shogi_maskable_ppo_vs_random/maskable_ppo_vs_random_black_20260525_140008/final_model.zip"

Write-Host "=== Training: MaskablePPO vs opponent pool (fresh 256x256 net, CUDA) ===" -ForegroundColor Cyan

& $exe train-maskable-ppo-vs-pool `
    --side BLACK `
    --timesteps 18000000 `
    --n-envs 24 `
    --seed 0 `
    --step-penalty -0.0001 `
    --opponent-model $frozen `
    --w-heuristic 0.5 --w-model 0.25 --w-random 0.25 `
    --net-arch 256,256 `
    --device cuda `
    --batch-size 1024 `
    --n-steps 2048 `
    --max-minutes 80 `
    --subproc

if ($LASTEXITCODE -ne 0) {
    Write-Host "Training exited with code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

$runDir = Get-ChildItem "checkpoints\animal_shogi_maskable_ppo_vs_pool" -Directory |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
$model = Join-Path $runDir.FullName "final_model.zip"

Write-Host ""
Write-Host "=== Evaluation 1/2: 200 games vs heuristic (the number that matters) ===" -ForegroundColor Cyan
& $exe evaluate-model --model $model --games 200 --side BLACK --opponent heuristic

Write-Host ""
Write-Host "=== Evaluation 2/2: 100 games vs random (regression check, was 100%) ===" -ForegroundColor Cyan
& $exe evaluate-model --model $model --games 100 --side BLACK --opponent random

Write-Host ""
Write-Host "=== Session complete ===" -ForegroundColor Green
Write-Host "Model: $model"
Write-Host "Copy the two evaluation result blocks above back to Claude for review."

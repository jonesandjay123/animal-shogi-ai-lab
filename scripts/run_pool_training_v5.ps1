# v5 iterated self-play session: warm-start from v4, train against frozen v4.
# Run from anywhere:  powershell -ExecutionPolicy Bypass -File scripts\run_pool_training_v5.ps1
# Total wall-clock: ~80 min training (auto-stops on time budget) + ~10 min evaluation.
#
# Acceptance gate: v5 should beat frozen v4 head-to-head with >55% win rate.

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo
$env:PYTHONUNBUFFERED = "1"

$exe = Join-Path $repo ".venv\Scripts\animal-shogi-lab.exe"
$v4 = "checkpoints/animal_shogi_maskable_ppo_vs_pool/maskable_ppo_vs_pool_black_20260703_113517/final_model.zip"

Write-Host "=== Training v5: warm start from v4, opponent pool led by frozen v4 ===" -ForegroundColor Cyan

& $exe train-maskable-ppo-vs-pool `
    --side BLACK `
    --timesteps 18000000 `
    --n-envs 24 `
    --seed 1 `
    --step-penalty -0.0001 `
    --init-model $v4 `
    --opponent-model $v4 `
    --w-heuristic 0.3 --w-model 0.5 --w-random 0.2 `
    --device cuda `
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
Write-Host "=== Evaluation 1/3: 200 games vs frozen v4 (acceptance gate: >55%) ===" -ForegroundColor Cyan
& $exe evaluate-model --model $model --games 200 --side BLACK --opponent model --opponent-model $v4

Write-Host ""
Write-Host "=== Evaluation 2/3: 100 games vs heuristic (should stay ~100%) ===" -ForegroundColor Cyan
& $exe evaluate-model --model $model --games 100 --side BLACK --opponent heuristic

Write-Host ""
Write-Host "=== Evaluation 3/3: 100 games vs random (should stay ~100%) ===" -ForegroundColor Cyan
& $exe evaluate-model --model $model --games 100 --side BLACK --opponent random

Write-Host ""
Write-Host "=== Session complete ===" -ForegroundColor Green
Write-Host "Model: $model"
Write-Host "Copy the three evaluation result blocks above back to Claude for review."

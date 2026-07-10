# Pousse ResellPro sur GitHub
# Usage: .\scripts\push-github.ps1 -Username TON_USERNAME

param(
    [Parameter(Mandatory = $true)]
    [string]$Username,
    [string]$RepoName = "resellpro"
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$remote = "https://github.com/$Username/$RepoName.git"

Write-Host "Repo cible: $remote" -ForegroundColor Cyan

# Creer le repo sur GitHub si gh est installe
$gh = Get-Command gh -ErrorAction SilentlyContinue
if ($gh) {
    gh repo create $RepoName --public --source=. --remote=origin --push
    Write-Host "Pousse via GitHub CLI." -ForegroundColor Green
    exit 0
}

# Sinon: creer le repo manuellement sur github.com/new puis pousser
$existing = git remote get-url origin 2>$null
if (-not $existing) {
    git remote add origin $remote
}

Write-Host ""
Write-Host "Si le repo n'existe pas encore:" -ForegroundColor Yellow
Write-Host "  1. Va sur https://github.com/new" -ForegroundColor Yellow
Write-Host "  2. Nom: $RepoName" -ForegroundColor Yellow
Write-Host "  3. Ne coche PAS 'Add README'" -ForegroundColor Yellow
Write-Host "  4. Create repository" -ForegroundColor Yellow
Write-Host ""
Write-Host "Puis appuie sur Entree pour pousser..." -ForegroundColor Yellow
Read-Host

git push -u origin main
Write-Host "Termine ! Repo: https://github.com/$Username/$RepoName" -ForegroundColor Green

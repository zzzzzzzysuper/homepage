# ============================================================
#  一键部署个人主页到 GitHub Pages
#
#  用法（在本文件所在目录打开 PowerShell）：
#      .\setup_github.ps1 -GitHubUser 你的用户名
#
#  可选参数：
#      -RepoName homepage        仓库名（默认 homepage，决定网址后缀）
#      -Email    you@example.com 替换页面里的邮箱占位内容
#      -SkipLogin                跳过登录步骤（已登录过时用）
#
#  脚本会：检查 gh → 登录 → 替换用户名占位 → 提交 → 建仓库 → 推送 → 开启 Pages
# ============================================================
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$GitHubUser,
    [string]$RepoName = 'homepage',
    [string]$Email    = '',
    [string]$Proxy    = 'http://127.0.0.1:7890',
    [switch]$NoProxy,
    [switch]$SkipLogin
)

$ErrorActionPreference = 'Stop'
$repo = $PSScriptRoot
Set-Location $repo

function Step($n, $t) { Write-Host "`n[$n] $t" -ForegroundColor Cyan }
function Ok($m)       { Write-Host "    OK  $m" -ForegroundColor Green }
function Warn($m)     { Write-Host "    --  $m" -ForegroundColor Yellow }
function Fail($m)     { Write-Host "    !!  $m" -ForegroundColor Red; exit 1 }

# ---------- 0. 定位工具 ----------
Step 0 '定位 git / gh'
$git = @('C:\Program Files\Git\cmd\git.exe') | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $git) { $git = (Get-Command git -ErrorAction SilentlyContinue).Source }
if (-not $git) { Fail '找不到 git.exe，请先安装 Git for Windows' }
$gh = @('C:\Program Files\GitHub CLI\gh.exe') | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $gh) { $gh = (Get-Command gh -ErrorAction SilentlyContinue).Source }
if (-not $gh) { Fail '找不到 gh.exe，请先安装 GitHub CLI（winget install GitHub.cli）' }
Ok "git = $git"
Ok "gh  = $gh"

# 有些网络（含本机）直连 github.com 会超时，需要走本地代理；
# 这里先探测代理端口，通得过才启用，避免在没有代理的机器上误设。
$useProxy = $false
if (-not $NoProxy -and $Proxy) {
    $hp = $Proxy -replace '^https?://', ''
    $hp = $hp -replace '/.*$', ''
    $parts = $hp.Split(':')
    $ph = $parts[0]; $pp = [int]$parts[1]
    try {
        $c = New-Object System.Net.Sockets.TcpClient
        $c.Connect($ph, $pp)
        $c.Close()
        $useProxy = $true
    } catch { $useProxy = $false }
}
if ($useProxy) {
    $env:HTTPS_PROXY = $Proxy
    $env:HTTP_PROXY  = $Proxy
    & $git config http.proxy  $Proxy
    & $git config https.proxy $Proxy
    Ok "代理 $Proxy 可用，已启用"
} else {
    Remove-Item Env:\HTTPS_PROXY -ErrorAction SilentlyContinue
    Remove-Item Env:\HTTP_PROXY  -ErrorAction SilentlyContinue
    & $git config --unset http.proxy  2>$null
    & $git config --unset https.proxy 2>$null
    Warn '未检测到可用代理，将直连 GitHub'
    Warn '（若推送/登录超时，改用： .\setup_github.ps1 -GitHubUser 你的用户名 -Proxy http://127.0.0.1:7890 ）'
}

# ---------- 1. 登录 GitHub ----------
if (-not $SkipLogin) {
    Step 1 '登录 GitHub（会打开浏览器，请在浏览器里点授权）'
    & $gh auth status *> $null
    if ($LASTEXITCODE -ne 0) {
        & $gh auth login --hostname github.com --git-protocol https --web
        if ($LASTEXITCODE -ne 0) { Fail '登录未完成' }
    } else {
        Ok '已处于登录状态'
    }
}

Step 1.1 '校验账号'
$me = (& $gh api user --jq .login 2>$null)
if (-not $me) { Fail '无法读取当前账号，请确认已登录' }
Ok "当前 GitHub 账号：$me"
if ($me -ne $GitHubUser) {
    Warn "你传入的用户名是 $GitHubUser，但登录的是 $me —— 将以 $me 为准"
    $GitHubUser = $me
}

# ---------- 2. 把仓库里的占位用户名换成真实用户名 ----------
Step 2 '替换页面中的占位信息'
$utf8 = New-Object System.Text.UTF8Encoding($false)
$files = @('index.html', 'README.md', '个人简介.md')
foreach ($f in $files) {
    if (-not (Test-Path $f)) { continue }
    $txt = [System.IO.File]::ReadAllText((Resolve-Path $f), $utf8)
    $before = $txt
    $txt = $txt -replace 'zhangming\.github\.io/homepage', "$GitHubUser.github.io/$RepoName"
    $txt = $txt -replace 'github\.com/zhangming', "github.com/$GitHubUser"
    $txt = $txt -replace '你的用户名', $GitHubUser
    if ($Email) { $txt = $txt -replace 'zhangming@example\.com', $Email }
    if ($txt -ne $before) {
        [System.IO.File]::WriteAllText((Resolve-Path $f), $txt, $utf8)
        Ok "已更新 $f"
    } else {
        Warn "$f 无需改动"
    }
}

# ---------- 3. 提交 ----------
Step 3 '提交改动'
& $git add -A
$dirty = (& $git status --porcelain)
if ($dirty) {
    & $git commit -m "更新为真实 GitHub 用户名与站点地址" | Out-Null
    Ok '已提交'
} else {
    Warn '没有需要提交的改动'
}

# ---------- 4. 创建（或复用）远程仓库 ----------
Step 4 "创建远程仓库 $GitHubUser/$RepoName"
$exists = & $gh repo view "$GitHubUser/$RepoName" --json name --jq .name 2>$null
if ($exists) {
    Ok '仓库已存在，直接使用'
} else {
    & $gh repo create "$GitHubUser/$RepoName" --public --source=. --remote=origin --description "个人主页 · 使用 HTML/CSS 构建，托管于 GitHub Pages"
    if ($LASTEXITCODE -ne 0) { Fail '创建仓库失败' }
    Ok '仓库已创建'
}

# ---------- 5. 推送 ----------
Step 5 '推送到 GitHub'
$remoteUrl = "https://github.com/$GitHubUser/$RepoName.git"
$current = (& $git remote get-url origin 2>$null)
if ($current) {
    & $git remote set-url origin $remoteUrl
} else {
    & $git remote add origin $remoteUrl
}
& $git push -u origin main
if ($LASTEXITCODE -ne 0) { Fail '推送失败，请把上面的报错发我' }
Ok '推送成功'

# ---------- 6. 开启 GitHub Pages ----------
Step 6 '开启 GitHub Pages（main 分支根目录）'
$body = '{"source":{"branch":"main","path":"/"}}'
$body | & $gh api -X POST "repos/$GitHubUser/$RepoName/pages" --input - *> $null
if ($LASTEXITCODE -ne 0) {
    Warn 'POST 失败（通常表示 Pages 已经开启过），改为更新配置'
    $body | & $gh api -X PUT "repos/$GitHubUser/$RepoName/pages" --input - *> $null
}
Start-Sleep -Seconds 3
$url = (& $gh api "repos/$GitHubUser/$RepoName/pages" --jq .html_url 2>$null)

Write-Host ''
Write-Host '====================================================' -ForegroundColor Green
if ($url) { Write-Host "  站点地址： $url" -ForegroundColor Green }
else      { Write-Host "  站点地址： https://$GitHubUser.github.io/$RepoName/" -ForegroundColor Green }
Write-Host '====================================================' -ForegroundColor Green
Write-Host ''
Warn '首次部署需要 1-2 分钟，稍后刷新网址即可看到页面'
Warn "如果打开是 404：仓库 Settings -> Pages，确认 Branch = main、目录 = / (root)"
Warn '页面里的邮箱/电话/GitHub 链接仍是示例内容，建议改成你自己的'

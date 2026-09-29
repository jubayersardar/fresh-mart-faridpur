[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Resolve paths from this script, so invocation does not depend on the current folder.
$workspaceRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')).TrimEnd('\', '/')
$workspacePrefix = $workspaceRoot + [System.IO.Path]::DirectorySeparatorChar
$releaseRoot = [System.IO.Path]::GetFullPath((Join-Path $workspaceRoot 'dist'))

function Assert-WorkspacePath {
    param([Parameter(Mandatory = $true)][string] $Path)

    $resolvedPath = [System.IO.Path]::GetFullPath($Path)
    if (-not $resolvedPath.StartsWith($workspacePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path is outside the website workspace: $resolvedPath"
    }
    return $resolvedPath
}

function Assert-NoReparsePoint {
    param([Parameter(Mandatory = $true)][string] $Path)

    if ((Get-Item -LiteralPath $Path -Force).Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
        throw "Symbolic links and junctions are not allowed in release paths: $Path"
    }
}

$publicPages = @('index.html', 'about.html', 'products.html', 'gallery.html', 'contact.html')
$detailPages = @(Get-ChildItem -LiteralPath $workspaceRoot -Filter 'product-*.html' -File |
    Where-Object { $_.Name -cmatch '^product-[a-z0-9]+(?:-[a-z0-9]+)*\.html$' } |
    Sort-Object Name)
if ($detailPages.Count -eq 0) {
    throw 'No generated product detail pages were found. Build them before packaging.'
}
$publicPages += @($detailPages | ForEach-Object { $_.Name })
$publicDirectories = @{
    'css' = @('.css')
    'js' = @('.js')
    'assets' = @('.avif', '.gif', '.ico', '.jpeg', '.jpg', '.png', '.svg', '.webp', '.woff', '.woff2', '.ttf', '.otf')
}
$releaseFiles = [System.Collections.Generic.List[System.IO.FileInfo]]::new()

# Validate the whole public input before replacing a previous release.
Assert-NoReparsePoint -Path $workspaceRoot
foreach ($page in $publicPages) {
    $sourcePath = Assert-WorkspacePath -Path (Join-Path $workspaceRoot $page)
    if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
        throw "Required public page is missing: $page"
    }
    Assert-NoReparsePoint -Path $sourcePath
    $releaseFiles.Add((Get-Item -LiteralPath $sourcePath))
}

foreach ($directoryName in $publicDirectories.Keys) {
    $sourceDirectory = Assert-WorkspacePath -Path (Join-Path $workspaceRoot $directoryName)
    if (-not (Test-Path -LiteralPath $sourceDirectory -PathType Container)) {
        throw "Required public directory is missing: $directoryName"
    }
    Assert-NoReparsePoint -Path $sourceDirectory
    $sourceItems = @(Get-ChildItem -LiteralPath $sourceDirectory -Recurse -Force)
    foreach ($item in $sourceItems) {
        $null = Assert-WorkspacePath -Path $item.FullName
        Assert-NoReparsePoint -Path $item.FullName
        if ($item.PSIsContainer) { continue }

        $relativePath = $item.FullName.Substring($workspacePrefix.Length)
        if ($relativePath -match '(^|[\\/])(data|tools|tests?|runtime|node_modules|\.git|\.venv|__pycache__)([\\/]|$)' -or
            $item.Name -match '\.(test|spec)\.') {
            continue
        }
        $isPublicAsset = $publicDirectories[$directoryName] -contains $item.Extension.ToLowerInvariant()
        $isFontLicense = $directoryName -eq 'assets' -and
            $item.Name -match '^(OFL|.*-OFL|LICENSE[^\\/]*)\.txt$'
        if ($isPublicAsset -or $isFontLicense) {
            $releaseFiles.Add($item)
        }
    }
}

$null = Assert-WorkspacePath -Path $releaseRoot
if ($releaseRoot -ne (Join-Path $workspaceRoot 'dist')) {
    throw 'The release target must be the workspace dist directory.'
}

if (Test-Path -LiteralPath $releaseRoot) {
    if (-not (Test-Path -LiteralPath $releaseRoot -PathType Container)) {
        throw "The release target is not a directory: $releaseRoot"
    }
    Assert-NoReparsePoint -Path $releaseRoot
    foreach ($existingItem in @(Get-ChildItem -LiteralPath $releaseRoot -Recurse -Force)) {
        $null = Assert-WorkspacePath -Path $existingItem.FullName
        Assert-NoReparsePoint -Path $existingItem.FullName
    }
    # This fixed, fully verified target is the only directory the script removes.
    Remove-Item -LiteralPath $releaseRoot -Recurse -Force
}
$null = New-Item -ItemType Directory -Path $releaseRoot

foreach ($sourceFile in $releaseFiles) {
    $relativePath = $sourceFile.FullName.Substring($workspacePrefix.Length)
    $destinationPath = Assert-WorkspacePath -Path (Join-Path $releaseRoot $relativePath)
    if (-not $destinationPath.StartsWith($releaseRoot + [System.IO.Path]::DirectorySeparatorChar,
            [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Copy target is outside the release directory: $destinationPath"
    }
    $destinationDirectory = Split-Path -Path $destinationPath -Parent
    if (-not (Test-Path -LiteralPath $destinationDirectory -PathType Container)) {
        $null = New-Item -ItemType Directory -Path $destinationDirectory -Force
    }
    Copy-Item -LiteralPath $sourceFile.FullName -Destination $destinationPath -Force
}

$deploymentReadme = @'
Fresh Mart Faridpur - public website release

Upload the contents of this directory to your static hosting site's web root.
Keep css/, js/, and assets/ beside the HTML pages, with their paths unchanged.
Set index.html as the default page and enable HTTPS on your hosting provider.
The pages use UTF-8 and include local fonts; no application server or installation is required.

This package contains only public pages, styles, scripts, images, fonts, and their licenses.
Private data/, the local preview server, tools/, tests, and runtime files are excluded.
Do not upload the parent source workspace.

After uploading, check the home page, navigation, product links, and contact links
on both a phone and a desktop browser.
'@
$readmePath = Assert-WorkspacePath -Path (Join-Path $releaseRoot 'README-DEPLOYMENT.txt')
[System.IO.File]::WriteAllText($readmePath, $deploymentReadme + [Environment]::NewLine,
    [System.Text.UTF8Encoding]::new($false))

Write-Host ("Public release ready: {0}" -f $releaseRoot)
Write-Host ("Packaged {0} public files plus the deployment instructions." -f $releaseFiles.Count)

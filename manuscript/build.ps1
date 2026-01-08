$ErrorActionPreference = "Stop"

$manu = $PSScriptRoot
$outDir = Join-Path $manu "build"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$book = Join-Path $manu "book.txt"
if (!(Test-Path $book)) {
  throw "book.txt not found at: $book"
}

$files = Get-Content $book |
  ForEach-Object { $_.Trim() } |
  Where-Object { $_ -ne "" -and -not $_.StartsWith("#") } |
  ForEach-Object { Join-Path $manu $_ }

# Hızlı kontrol: eksik dosya var mı?
$missing = $files | Where-Object { -not (Test-Path $_) }
if ($missing.Count -gt 0) {
  throw "Missing chapter files:`n$($missing -join "`n")"
}

$docxOut = Join-Path $outDir "thesis.docx"
$mdOut   = Join-Path $outDir "thesis.md"

# Kaynak yolu: görselleri ve tabloları bulsun
$resourcePath = "$manu;$($manu)\figures;$($manu)\tables;$($manu)\chapters"

pandoc @files `
  --from markdown `
  --resource-path "$resourcePath" `
  -o "$docxOut"

pandoc @files `
  --from markdown `
  --resource-path "$resourcePath" `
  -o "$mdOut"

Write-Host "Built:"
Write-Host " - $docxOut"
Write-Host " - $mdOut"

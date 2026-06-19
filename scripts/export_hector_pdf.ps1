<#
.SYNOPSIS
    Export a HECTOR thesis DOCX to PDF via the canonical Microsoft Word COM
    ExportAsFixedFormat (wdFormatPDF = 17) pipeline.

.DESCRIPTION
    This is the committed, repeatable generator for the HECTOR thesis PDF. It
    uses the SAME mechanism as scripts/gen_final_submission.py's export_pdf()
    (Word COM + ExportAsFixedFormat, format 17) and deliberately does NOT use
    ReportLab, LibreOffice/soffice, pandoc, or python-docx rendering. It is
    packaged as PowerShell because the repository's .venv Python interpreter is
    currently non-functional (its base interpreter was removed); the export
    itself is a pure Word COM operation, so no Python is required.

    Document-only: it does not run experiments and does not modify evidence
    artifacts, figures, tables, numerical results, or bibliography content.

    The source DOCX is opened READ-ONLY and is NEVER saved, so it cannot be
    mutated. A SHA256 check before/after the export enforces this invariant and
    aborts if the source changed for any reason.

.PARAMETER Docx
    Path to the source HECTOR DOCX. Defaults to the v3c manuscript.

.PARAMETER Pdf
    Output PDF path. Defaults to the source path with a .pdf extension.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts/export_hector_pdf.ps1
#>
[CmdletBinding()]
param(
    [string]$Docx = '',
    [string]$Pdf  = ''
)

$ErrorActionPreference = 'Stop'

# Resolve the default DOCX relative to this script's own location. ($PSScriptRoot
# can be empty when referenced in a param() default under Windows PowerShell 5.1,
# so resolve it here in the body using $PSCommandPath.)
if (-not $Docx) {
    $scriptDir = Split-Path -Parent $PSCommandPath
    $Docx = Join-Path $scriptDir '..\manuscript\Onur_Emiroglu_MSc_Thesis_HECTOR_v3c.docx'
}

$Docx = (Resolve-Path -LiteralPath $Docx).Path
if (-not $Pdf) { $Pdf = [System.IO.Path]::ChangeExtension($Docx, '.pdf') }

Write-Output "Source DOCX : $Docx"
Write-Output "Output PDF  : $Pdf"

# --- invariant: never mutate the source DOCX ---
$beforeHash = (Get-FileHash -LiteralPath $Docx -Algorithm SHA256).Hash

$tmp = [System.IO.Path]::ChangeExtension($Pdf, '.tmp.pdf')
if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force }

$word = $null
$doc  = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0   # wdAlertsNone

    # Open READ-ONLY (ConfirmConversions=$false, ReadOnly=$true, AddToRecentFiles=$false)
    $doc = $word.Documents.Open($Docx, $false, $true, $false)

    # Update Word fields + any Table of Contents in-memory only (no-op when the
    # document has no fields/TOC). The document is read-only and never saved, so
    # this cannot alter the source DOCX on disk; it only affects the exported PDF.
    try { $doc.Fields.Update() | Out-Null } catch {}
    foreach ($toc in $doc.TablesOfContents) { try { $toc.Update() | Out-Null } catch {} }

    # Canonical export: wdExportFormatPDF = 17
    $doc.ExportAsFixedFormat($tmp, 17)

    $doc.Close($false)   # discard; never save -> source DOCX unchanged
    $doc = $null
}
finally {
    if ($doc)  { try { $doc.Close($false) } catch {} }
    if ($word) { try { $word.Quit() } catch {} }
    if ($doc)  { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($doc) }
    if ($word) { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) }
    [System.GC]::Collect(); [System.GC]::WaitForPendingFinalizers()
}

if (-not (Test-Path -LiteralPath $tmp)) { throw "Export failed: temporary PDF was not created." }
Move-Item -LiteralPath $tmp -Destination $Pdf -Force

$afterHash = (Get-FileHash -LiteralPath $Docx -Algorithm SHA256).Hash
if ($beforeHash -ne $afterHash) {
    throw "Source DOCX was modified during export (SHA256 changed): $Docx"
}

$pdfInfo = Get-Item -LiteralPath $Pdf
Write-Output ("Wrote PDF   : {0} ({1} bytes)" -f $Pdf, $pdfInfo.Length)
Write-Output ("Source DOCX unchanged (SHA256 {0})" -f $beforeHash)

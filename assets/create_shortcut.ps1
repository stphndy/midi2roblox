# Creates "Roblox Piano" shortcuts on the Desktop and in the Start menu.
# Run via "Create Desktop Shortcut.bat" in the project folder.
$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent $PSScriptRoot
$target  = Join-Path $project 'midi2roblox.bat'
$icon    = Join-Path $PSScriptRoot 'midi2roblox.ico'
$shell   = New-Object -ComObject WScript.Shell

$places = @(
    [Environment]::GetFolderPath('Desktop'),
    [Environment]::GetFolderPath('Programs')
)
foreach ($dir in $places) {
    $lnk = $shell.CreateShortcut((Join-Path $dir 'Roblox Piano.lnk'))
    $lnk.TargetPath       = $target
    $lnk.WorkingDirectory = $project
    $lnk.IconLocation     = "$icon,0"
    $lnk.Description      = 'Play Roblox piano games with the MIDI keyboard'
    $lnk.Save()
    Write-Host "Created: $($lnk.FullName)"
}

$parent = (get-item $PSScriptRoot ).parent.FullName
$python_path = Get-Content -Path $parent/env/python_path
$main_path = $parent + "\main.py"

$cmd = "& `"{0}`" `"{1}`" moonlight_secondary_monitor 1 wall_mounted_and_work_laptop" -f $python_path, $main_path
Invoke-Expression $cmd
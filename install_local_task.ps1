# Generated with GitHub Copilot - [Tracking ID: Hexure-Copilot]
# Registers a Task Scheduler job (current user, no admin needed) that runs publish_local.py every 10 minutes.
$dir = $PSScriptRoot
$py = (Get-Command python).Source
$action = New-ScheduledTaskAction -Execute $py -Argument "publish_local.py" -WorkingDirectory $dir
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 10)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 8)
Register-ScheduledTask -TaskName "PhonePricesLocalPublish" -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
Write-Host "Task 'PhonePricesLocalPublish' registered: runs every 10 minutes while you are logged in."

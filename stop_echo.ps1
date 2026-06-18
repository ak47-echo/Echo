$ErrorActionPreference = "Continue"

$ports = @(8000, 5173)
$stopped = @()

foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    $processIds = $connections |
        Where-Object { $_.OwningProcess -and $_.OwningProcess -ne 0 } |
        Select-Object -ExpandProperty OwningProcess -Unique

    if (-not $processIds) {
        Write-Host "No process found on port $port."
        continue
    }

    foreach ($processId in $processIds) {
        try {
            $process = Get-Process -Id $processId -ErrorAction Stop
            Stop-Process -Id $processId -Force -ErrorAction Stop
            $message = "Stopped $($process.ProcessName) (PID $processId) on port $port."
            $stopped += $message
            Write-Host $message
        }
        catch {
            Write-Host "Could not stop PID $processId on port ${port}: $($_.Exception.Message)"
        }
    }
}

if (-not $stopped) {
    Write-Host "No Echo port processes were stopped."
}

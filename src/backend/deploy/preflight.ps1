$ErrorActionPreference = 'Stop'
Get-CimInstance Win32_ComputerSystem | Select-Object NumberOfLogicalProcessors, @{Name='RAM_GiB'; Expression={[math]::Round($_.TotalPhysicalMemory / 1GB, 1)}}
Get-PSDrive C | Select-Object Name, @{Name='Free_GiB'; Expression={[math]::Round($_.Free / 1GB, 1)}}
wsl --version
docker version --format '{{.Server.Version}}'
docker compose version
Get-Service sshd -ErrorAction SilentlyContinue | Select-Object Name, Status, StartType
Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object LocalPort -In 5432, 9000, 9001, 3000, 22 | Select-Object LocalAddress, LocalPort, OwningProcess

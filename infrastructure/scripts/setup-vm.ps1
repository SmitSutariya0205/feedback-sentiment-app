# setup-vm.ps1 — Provisioning script for VM Scale Set instances
Write-Host "Starting VM setup script..."

# 1. Install IIS Web Server with Management Tools
Install-WindowsFeature -name Web-Server -IncludeManagementTools
Write-Host "IIS Web Server installed successfully."

# 2. Download and install Python 3.12 (silent installation)
$pythonUrl = "https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe"
$installerPath = "C:\Windows\Temp\python-installer.exe"

Write-Host "Downloading Python 3.12..."
Invoke-WebRequest -Uri $pythonUrl -OutFile $installerPath

Write-Host "Installing Python 3.12..."
Start-Process -FilePath $installerPath -Wait -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1"
Write-Host "Python 3.12 installed."

# 3. Restart IIS services
net stop was /y
net start w3svc
Write-Host "VM setup complete and ready to host FastAPI / Nginx traffic."

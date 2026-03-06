# Complete Audit System Deployment Guide
## SSH Reverse Tunnel Architecture (Windows → Linux)

---

## 📋 TABLE OF CONTENTS

1. [System Architecture](#system-architecture)
2. [Prerequisites](#prerequisites)
3. [Installation Steps](#installation-steps)
4. [Configuration](#configuration)
5. [Running the System](#running-the-system)
6. [Troubleshooting](#troubleshooting)
7. [Security Considerations](#security-considerations)

---

## 🏗️ SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────┐
│         WINDOWS MACHINE                 │
│  ┌───────────────────────────────────┐  │
│  │ 1. Screenshot Flask Server        │  │
│  │    (localhost:5000)               │  │
│  │                                   │  │
│  │ 2. SSH Tunnel Manager             │  │
│  │    Creates: Linux:5000 →          │  │
│  │             Windows:localhost:5000│  │
│  └───────────────────────────────────┘  │
└──────────────┬──────────────────────────┘
               │
               │ SSH Tunnel (Port 22)
               │ Windows initiates connection
               │
┌──────────────┴──────────────────────────┐
│         LINUX SERVER                    │
│  ┌───────────────────────────────────┐  │
│  │ Audit Script (audit.py)           │  │
│  │ - Reads audit_config.json         │  │
│  │ - Executes commands               │  │
│  │ - Requests screenshots via        │  │
│  │   http://localhost:5000           │  │
│  │ - Generates reports               │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

**Key Feature**: No firewall changes needed! Uses outbound SSH (port 22) which is already allowed.

---

## ✅ PREREQUISITES

### On Windows Machine:

1. **Python 3.8 or higher**
   ```powershell
   python --version
   # Should show: Python 3.8.x or higher
   ```

2. **Windows OpenSSH Client** (Built into Windows 10/11)
   ```powershell
   # Check if SSH is available
   ssh -V
   # Should show: OpenSSH_for_Windows_x.x
   ```

3. **Network connectivity** to Linux server (outbound SSH port 22)

4. **Python libraries** (will be installed in setup)

### On Linux Server:

1. **SSH Server running**
   ```bash
   sudo systemctl status sshd
   # Should show: active (running)
   ```

2. **Python 3.8 or higher**
   ```bash
   python3 --version
   ```

3. **SSH tunnel forwarding enabled** (usually enabled by default)
   ```bash
   # Check /etc/ssh/sshd_config
   grep "AllowTcpForwarding" /etc/ssh/sshd_config
   # Should show: AllowTcpForwarding yes (or commented out = default yes)
   ```

4. **User account** with SSH access and sudo privileges (for installing packages)

---

## 📦 INSTALLATION STEPS

### STEP 1: Windows Setup

#### 1.1 Create Project Directory
```powershell
# Open PowerShell as Administrator
cd C:\
New-Item -Path "C:\AuditSystem" -ItemType Directory
cd C:\AuditSystem
```

#### 1.2 Install Python Dependencies
```powershell
# Create requirements file
@"
flask==3.0.0
pyautogui==0.9.54
pillow==10.1.0
werkzeug==3.0.1
"@ | Out-File -FilePath requirements.txt -Encoding utf8

# Install dependencies
pip install -r requirements.txt
```

#### 1.3 Download System Files
- Copy `windows_screenshot_service.py` to `C:\AuditSystem\`
- Copy `windows_start_audit.py` to `C:\AuditSystem\`
- Copy `windows_config.json` to `C:\AuditSystem\`

#### 1.4 Configure Windows Settings
Edit `C:\AuditSystem\windows_config.json`:
```json
{
    "linux_server": {
        "host": "your-linux-server.example.com",
        "username": "your-linux-username",
        "port": 22
    },
    "screenshot_settings": {
        "local_port": 5000,
        "save_directory": "C:\\AuditScreenshots"
    }
}
```

### STEP 2: Linux Setup

#### 2.1 Create Project Directory
```bash
# SSH to your Linux server
ssh your-username@linux-server.example.com

# Create project directory
mkdir -p ~/audit-system
cd ~/audit-system
```

#### 2.2 Install Python Dependencies
```bash
# Create requirements file
cat > requirements.txt << 'EOF'
requests==2.31.0
EOF

# Install dependencies
pip3 install -r requirements.txt --user
```

#### 2.3 Download System Files
- Copy `linux_audit.py` to `~/audit-system/`
- Copy `audit_config.json` to `~/audit-system/`

#### 2.4 Configure Linux Settings
Edit `~/audit-system/audit_config.json`:
```json
{
    "audit_metadata": {
        "auditor_name": "Your Name",
        "environment": "production",
        "compliance_framework": "SOX/ISO27001"
    },
    "screenshot_service": {
        "url": "http://localhost:5000",
        "timeout": 10
    },
    "commands": [
        {
            "name": "System Hostname",
            "command": "hostname",
            "description": "Verify server identity",
            "critical": true
        },
        {
            "name": "System Uptime",
            "command": "uptime",
            "description": "Check last reboot time",
            "critical": true
        },
        {
            "name": "Disk Usage",
            "command": "df -h",
            "description": "Verify storage capacity",
            "critical": true
        }
    ],
    "output_options": {
        "log_directory": "~/audit-logs",
        "generate_html_report": true,
        "generate_json_log": true
    }
}
```

#### 2.5 Make Scripts Executable
```bash
chmod +x ~/audit-system/linux_audit.py
```

### STEP 3: SSH Key Setup (Recommended)

For automated authentication without password prompts:

#### 3.1 Generate SSH Key on Windows
```powershell
# Generate SSH key pair (press Enter for all prompts)
ssh-keygen -t ed25519 -C "audit-system"
# Keys saved to: C:\Users\YourUsername\.ssh\id_ed25519
```

#### 3.2 Copy Public Key to Linux Server
```powershell
# Method 1: Using ssh-copy-id (if available)
ssh-copy-id -i $env:USERPROFILE\.ssh\id_ed25519.pub your-username@linux-server

# Method 2: Manual copy
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh your-username@linux-server "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

#### 3.3 Test SSH Key Authentication
```powershell
# Should connect without password prompt
ssh your-username@linux-server "echo Connection successful"
```

---

## ⚙️ CONFIGURATION

### Audit Commands Configuration

Edit `audit_config.json` on Linux to add your standardized audit commands:

```json
{
    "commands": [
        {
            "name": "System Information",
            "command": "uname -a",
            "description": "Display system information",
            "critical": true
        },
        {
            "name": "User List",
            "command": "cat /etc/passwd | grep -v nologin | tail -10",
            "description": "List recent user accounts",
            "critical": true
        },
        {
            "name": "Network Connections",
            "command": "netstat -tuln | head -20",
            "description": "Show listening ports",
            "critical": true
        },
        {
            "name": "Running Processes",
            "command": "ps aux --sort=-%mem | head -15",
            "description": "Top processes by memory",
            "critical": false
        },
        {
            "name": "Last Login",
            "command": "last -10",
            "description": "Recent login history",
            "critical": true
        }
    ]
}
```

### Screenshot Settings

Adjust screenshot quality/format in `windows_screenshot_service.py` if needed:

```python
# Default: PNG format, high quality
screenshot.save(filepath, format='PNG', optimize=True)

# For smaller files (lower quality):
screenshot.save(filepath, format='JPEG', quality=85)
```

---

## 🚀 RUNNING THE SYSTEM

### Complete Workflow

#### STEP 1: Start Windows Components (On Windows Machine)

**Option A: Automated Startup (Recommended)**
```powershell
# Open PowerShell in C:\AuditSystem
cd C:\AuditSystem
python windows_start_audit.py
```

This will:
1. ✅ Start Flask screenshot service
2. ✅ Establish SSH reverse tunnel to Linux
3. ✅ Wait for audit execution
4. ✅ Display status dashboard

**Option B: Manual Startup**
```powershell
# Terminal 1: Start screenshot service
cd C:\AuditSystem
python windows_screenshot_service.py

# Terminal 2: Create SSH tunnel
ssh -R 5000:localhost:5000 -N your-username@linux-server
```

#### STEP 2: Verify Tunnel (On Linux Server)

```bash
# SSH to Linux server (in new terminal)
ssh your-username@linux-server

# Test screenshot service connectivity
curl http://localhost:5000/health
# Expected: {"status":"ok","timestamp":"2026-03-06T17:42:00.123456"}
```

If you get connection refused, the tunnel is not established. Check Windows SSH connection.

#### STEP 3: Run Audit (On Linux Server)

```bash
cd ~/audit-system
python3 linux_audit.py
```

**Expected Output:**
```
═══════════════════════════════════════════════════════
        AUTOMATED AUDIT SYSTEM
═══════════════════════════════════════════════════════
Session ID: audit-20260306-174230
Auditor: Your Name
Environment: production
═══════════════════════════════════════════════════════

[✓] Screenshot service health check: OK

Starting audit execution...

[1/5] Executing: hostname
  ├─ Output: server01.example.com
  ├─ Exit Code: 0
  ├─ Duration: 125ms
  └─ Screenshot: 001_hostname_20260306-174231.png ✓

[2/5] Executing: uptime
  ├─ Output: 17:42:31 up 45 days, 12:30, 3 users, load average: 0.15, 0.22, 0.18
  ├─ Exit Code: 0
  ├─ Duration: 98ms
  └─ Screenshot: 002_uptime_20260306-174231.png ✓

...

═══════════════════════════════════════════════════════
Audit completed successfully!
═══════════════════════════════════════════════════════
Total commands: 5
Successful: 5
Failed: 0
Total duration: 3.2 seconds

Results saved to:
  📄 Log: ~/audit-logs/audit-20260306-174230/audit_log.json
  📊 Report: ~/audit-logs/audit-20260306-174230/audit_report.html
  📷 Screenshots: On Windows at C:\AuditScreenshots\audit-20260306-174230\
═══════════════════════════════════════════════════════
```

#### STEP 4: Review Results

**On Linux:**
```bash
# View JSON log
cat ~/audit-logs/audit-20260306-174230/audit_log.json | python3 -m json.tool

# View HTML report (if desktop environment available)
firefox ~/audit-logs/audit-20260306-174230/audit_report.html

# Or copy to Windows for viewing
scp ~/audit-logs/audit-20260306-174230/audit_report.html your-windows-username@windows-machine:C:/AuditSystem/
```

**On Windows:**
```powershell
# View screenshots
explorer C:\AuditScreenshots\audit-20260306-174230\

# Screenshots are named: 001_hostname_timestamp.png, 002_uptime_timestamp.png, etc.
```

#### STEP 5: Stop Services (When Done)

**On Windows:**
```powershell
# If using automated script (windows_start_audit.py)
# Press Ctrl+C in PowerShell window

# If using manual method:
# Close both PowerShell terminals (Flask + SSH tunnel)
```

---

## 🔧 TROUBLESHOOTING

### Problem 1: "Connection refused" when testing tunnel

**Symptoms:**
```bash
curl http://localhost:5000/health
# curl: (7) Failed to connect to localhost port 5000: Connection refused
```

**Solutions:**

1. **Check if Flask service is running on Windows**
   ```powershell
   # On Windows, look for Flask process
   Get-Process python
   ```

2. **Check if SSH tunnel is established**
   ```powershell
   # On Windows, check SSH connection
   Get-Process ssh
   ```

3. **Check SSH tunnel forwarding on Linux**
   ```bash
   # On Linux, check if port is listening
   ss -tlnp | grep 5000
   # Should show: 127.0.0.1:5000 ... users:(("sshd",pid=xxxx))
   ```

4. **Verify SSH config allows tunneling**
   ```bash
   # On Linux server
   grep "AllowTcpForwarding" /etc/ssh/sshd_config
   # Should be "yes" or commented out (default is yes)
   
   # If changed, restart SSH
   sudo systemctl restart sshd
   ```

### Problem 2: SSH authentication fails / password prompts

**Symptoms:**
```powershell
ssh your-username@linux-server
# Password: (prompts for password)
```

**Solutions:**

1. **Verify SSH key is loaded**
   ```powershell
   # On Windows, check SSH agent
   ssh-add -l
   # Should show your key fingerprint
   ```

2. **Add key to SSH agent**
   ```powershell
   # Start SSH agent (run as Administrator)
   Get-Service ssh-agent | Set-Service -StartupType Automatic
   Start-Service ssh-agent
   
   # Add your key
   ssh-add $env:USERPROFILE\.ssh\id_ed25519
   ```

3. **Verify public key on Linux**
   ```bash
   # On Linux
   cat ~/.ssh/authorized_keys
   # Should contain your public key from Windows
   ```

4. **Check permissions**
   ```bash
   # On Linux
   chmod 700 ~/.ssh
   chmod 600 ~/.ssh/authorized_keys
   ```

### Problem 3: Screenshot capture fails

**Symptoms:**
```
Screenshot: error ✗
```

**Solutions:**

1. **Check PyAutoGUI can access display**
   ```powershell
   # On Windows, test screenshot manually
   python -c "import pyautogui; pyautogui.screenshot().save('test.png'); print('Success')"
   ```

2. **Ensure Windows is unlocked** (locked screen prevents screenshot)

3. **Check disk space**
   ```powershell
   # On Windows
   Get-PSDrive C | Select-Object Used,Free
   ```

4. **Check screenshot directory permissions**
   ```powershell
   # On Windows
   Test-Path C:\AuditScreenshots
   # Should return: True
   ```

### Problem 4: Audit script hangs/times out

**Symptoms:**
```
[1/5] Executing: hostname
  └─ (waiting...)
```

**Solutions:**

1. **Increase timeout in audit_config.json**
   ```json
   {
       "screenshot_service": {
           "timeout": 30  // Increase from 10 to 30 seconds
       }
   }
   ```

2. **Check command syntax**
   ```bash
   # Test command manually
   bash -c "hostname"
   ```

3. **Check network latency**
   ```bash
   # On Linux, test response time
   time curl http://localhost:5000/health
   ```

### Problem 5: Windows can't establish SSH tunnel

**Symptoms:**
```powershell
ssh -R 5000:localhost:5000 -N your-username@linux-server
# ssh: connect to host linux-server port 22: Connection refused
```

**Solutions:**

1. **Verify Linux server is reachable**
   ```powershell
   # On Windows
   Test-NetConnection -ComputerName linux-server.example.com -Port 22
   ```

2. **Check corporate proxy settings**
   ```powershell
   # If behind corporate proxy, configure SSH to use proxy
   # Edit: C:\Users\YourUsername\.ssh\config
   
   Host linux-server
       ProxyCommand connect-proxy -H proxy.company.com:8080 %h %p
   ```

3. **Use IP address instead of hostname**
   ```powershell
   # Instead of hostname, use IP
   ssh -R 5000:localhost:5000 -N username@192.168.1.100
   ```

### Problem 6: Permission denied errors on Linux

**Symptoms:**
```bash
python3 linux_audit.py
# PermissionError: [Errno 13] Permission denied: '/home/user/audit-logs'
```

**Solutions:**

1. **Create directories with correct permissions**
   ```bash
   mkdir -p ~/audit-logs
   chmod 755 ~/audit-logs
   ```

2. **Check Python script permissions**
   ```bash
   chmod +x ~/audit-system/linux_audit.py
   ```

---

## 🔒 SECURITY CONSIDERATIONS

### 1. SSH Key Protection

✅ **DO:**
- Use strong passphrases for SSH keys (optional but recommended)
- Store keys in secure location: `C:\Users\YourUsername\.ssh\`
- Use `ssh-agent` to avoid re-entering passphrase

❌ **DON'T:**
- Share private keys via email/chat
- Store keys in shared network drives
- Commit keys to Git repositories

### 2. Audit Log Protection

✅ **DO:**
- Restrict audit log directory permissions: `chmod 700 ~/audit-logs`
- Archive old audit sessions: `tar -czf audit-archive.tar.gz ~/audit-logs/`
- Review logs regularly for anomalies

❌ **DON'T:**
- Store logs in publicly accessible locations
- Share screenshots containing sensitive data unencrypted
- Keep audit logs indefinitely without review

### 3. Network Security

✅ **DO:**
- Use SSH key authentication (not passwords)
- Keep OpenSSH client/server updated
- Monitor SSH access logs: `/var/log/auth.log`

❌ **DON'T:**
- Use default/weak passwords
- Allow root SSH login
- Expose SSH to public internet without additional protection

### 4. Audit Commands Security

✅ **DO:**
- Review audit commands before execution
- Use read-only commands when possible
- Log all command execution

❌ **DON'T:**
- Execute commands that modify system state
- Run untrusted commands from external sources
- Include passwords/secrets in command output

### 5. Screenshot Data Protection

✅ **DO:**
- Encrypt screenshot folders if containing sensitive data
- Review screenshots before sharing
- Delete screenshots after audit completion (if not needed)

❌ **DON'T:**
- Store screenshots with sensitive credentials visible
- Share screenshots via unsecured channels
- Keep screenshots longer than retention policy requires

---

## 📚 ADDITIONAL RESOURCES

### Log Files

- **Windows Flask logs**: Displayed in PowerShell console
- **Linux audit logs**: `~/audit-logs/[session-id]/audit_log.json`
- **SSH connection logs**: `C:\Users\YourUsername\.ssh\` (Windows), `/var/log/auth.log` (Linux)

### Useful Commands

**Check system status:**
```bash
# On Linux
systemctl status sshd          # SSH server status
ss -tlnp | grep 5000          # Check if tunnel port is open
ps aux | grep python          # Check running Python processes
```

```powershell
# On Windows
Get-Process python            # Check Python processes
Get-Process ssh               # Check SSH tunnel process
Test-NetConnection -ComputerName linux-server -Port 22  # Test connectivity
```

**Stop all processes:**
```bash
# On Linux
pkill -f linux_audit.py       # Stop audit script
```

```powershell
# On Windows
Stop-Process -Name python -Force     # Stop all Python processes
Get-Process ssh | Stop-Process       # Stop SSH tunnel
```

---

## 🎯 QUICK START CHECKLIST

Before running your first audit:

- [ ] Windows: Python 3.8+ installed
- [ ] Windows: Flask, PyAutoGUI, Pillow installed
- [ ] Windows: OpenSSH client available (`ssh -V` works)
- [ ] Windows: Config file updated with Linux server details
- [ ] Linux: SSH server running and accessible
- [ ] Linux: Python 3.8+ installed
- [ ] Linux: `requests` library installed
- [ ] Linux: Config file updated with audit commands
- [ ] SSH key authentication configured (optional but recommended)
- [ ] Test connection: `ssh your-username@linux-server` works
- [ ] Screenshot directory created: `C:\AuditScreenshots`
- [ ] Audit log directory created: `~/audit-logs`

---

## 📞 SUPPORT

If you encounter issues not covered in this guide:

1. **Check logs** for error messages
2. **Review troubleshooting section** above
3. **Test components individually** (Flask → SSH tunnel → Audit script)
4. **Verify network connectivity** between Windows and Linux
5. **Document the error** (copy exact error message, commands executed, system state)

---

**Deployment Guide Version:** 1.0  
**Last Updated:** March 6, 2026  
**Compatible With:** Windows 10/11, Linux (Ubuntu 20.04+, RHEL 8+, CentOS 8+)

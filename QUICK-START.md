# Quick Start Guide - Audit System with SSH Reverse Tunnel

## ⚡ Fast Setup (15 minutes)

### Windows Setup (5 minutes)

1. **Create directory and install dependencies**
   ```powershell
   # Open PowerShell as Administrator
   cd C:\
   mkdir AuditSystem
   cd AuditSystem
   
   # Create requirements file
   @"
   flask==3.0.0
   pyautogui==0.9.54
   pillow==10.1.0
   "@ | Out-File -FilePath requirements.txt -Encoding utf8
   
   # Install
   pip install -r requirements.txt
   ```

2. **Download files to C:\AuditSystem\**
   - `windows_screenshot_service.py`
   - `windows_start_audit.py`
   - `windows_config.json`

3. **Configure windows_config.json**
   ```json
   {
       "linux_server": {
           "host": "192.168.1.100",  ← Your Linux server IP
           "username": "your-username",  ← Your Linux username
           "port": 22
       },
       "screenshot_settings": {
           "local_port": 5000,
           "save_directory": "C:\\AuditScreenshots"
       }
   }
   ```

4. **Setup SSH key (recommended)**
   ```powershell
   # Generate key
   ssh-keygen -t ed25519 -C "audit-system"
   # Press Enter for all prompts
   
   # Copy to Linux
   type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh your-username@192.168.1.100 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
   
   # Test
   ssh your-username@192.168.1.100 "echo Success"
   ```

### Linux Setup (5 minutes)

1. **Create directory and install dependencies**
   ```bash
   mkdir -p ~/audit-system
   cd ~/audit-system
   
   # Install Python library
   pip3 install requests --user
   ```

2. **Download files to ~/audit-system/**
   - `linux_audit.py`
   - `audit_config.json`

3. **Make script executable**
   ```bash
   chmod +x ~/audit-system/linux_audit.py
   ```

4. **Configure audit_config.json**
   ```bash
   # Edit with your preferred editor
   nano ~/audit-system/audit_config.json
   
   # Update:
   # - auditor_name: Your name
   # - environment: production/staging/development
   # - Add/modify commands as needed
   ```

### Run Your First Audit (5 minutes)

**Step 1: Start Windows components**
```powershell
# On Windows, in C:\AuditSystem
python windows_start_audit.py
```

Expected output:
```
======================================================================
               AUTOMATED AUDIT SYSTEM
          Windows Component - SSH Reverse Tunnel
======================================================================
Started: 2026-03-06 17:42:00
======================================================================

Loading configuration...
✓ Configuration loaded

[1/2] Starting Flask screenshot service...
      ✓ Flask service running (PID: 12345)
      ✓ Listening on: http://localhost:5000

[2/2] Establishing SSH reverse tunnel...
      Target: your-username@192.168.1.100:22
      Tunnel: Linux:5000 → Windows:localhost:5000
      ✓ SSH tunnel established (PID: 12346)
      ✓ Linux server can access: http://localhost:5000

======================================================================
                        SYSTEM STATUS
======================================================================

📊 Components:
   Flask Service:     🟢 Running
   SSH Tunnel:        🟢 Connected

⚙️  Configuration:
   Linux Server:      your-username@192.168.1.100
   Screenshot Dir:    C:\AuditScreenshots
   Local Port:        5000

📝 Next Steps:
   1. SSH to your Linux server
   2. Verify tunnel: curl http://localhost:5000/health
   3. Run audit: python3 linux_audit.py
   4. Press Ctrl+C here when done to stop services

======================================================================
               System ready for audit execution
======================================================================
```

**Step 2: Test tunnel (on Linux)**
```bash
# SSH to Linux server (new terminal)
ssh your-username@192.168.1.100

# Test screenshot service
curl http://localhost:5000/health
```

Expected output:
```json
{"status":"ok","service":"Windows Screenshot Service","timestamp":"2026-03-06T17:42:30.123456"}
```

**Step 3: Run audit (on Linux)**
```bash
cd ~/audit-system
python3 linux_audit.py
```

Expected output:
```
======================================================================
                    AUTOMATED AUDIT SYSTEM
======================================================================
Session ID: audit-20260306-174230
Auditor: Your Name
Environment: production
Compliance: SOX/ISO27001/PCI-DSS
Started: 2026-03-06T17:42:30.123456
======================================================================

[✓] Performing health check on screenshot service...
    ✓ Screenshot service: OK

----------------------------------------------------------------------
Starting audit execution...

[1/12] Executing: hostname
  ├─ Output: server01.example.com
  ├─ Exit Code: 0
  ├─ Duration: 125ms
  └─ Screenshot: 001_hostname_20260306-174231.png ✓

[2/12] Executing: uptime
  ├─ Output: 17:42:31 up 45 days, 12:30, 3 users, load average: 0.15, 0.22, 0.18
  ├─ Exit Code: 0
  ├─ Duration: 98ms
  └─ Screenshot: 002_uptime_20260306-174231.png ✓

...

----------------------------------------------------------------------
Saving audit results...

  ✓ JSON log: /home/user/audit-logs/audit-20260306-174230/audit_log.json
  ✓ Text log: /home/user/audit-logs/audit-20260306-174230/audit_log.txt
  ✓ HTML report: /home/user/audit-logs/audit-20260306-174230/audit_report.html

======================================================================
Audit completed successfully!
======================================================================
Total commands: 12
Successful: 12
Failed: 0
Total duration: 8.3 seconds

Results saved to:
  📄 Log: ~/audit-logs/audit-20260306-174230/audit_log.json
  📊 Report: ~/audit-logs/audit-20260306-174230/audit_report.html
  📷 Screenshots: On Windows at C:\AuditScreenshots\audit-20260306-174230\
======================================================================
```

**Step 4: Review results**

```bash
# On Linux: View HTML report
firefox ~/audit-logs/audit-20260306-174230/audit_report.html
```

```powershell
# On Windows: View screenshots
explorer C:\AuditScreenshots\audit-20260306-174230\
```

**Step 5: Stop services**
```powershell
# On Windows: Press Ctrl+C in PowerShell window
```

---

## 🎯 File Checklist

### Windows (C:\AuditSystem\)
- [ ] `windows_screenshot_service.py`
- [ ] `windows_start_audit.py`
- [ ] `windows_config.json` (configured with your Linux server details)
- [ ] `requirements.txt`
- [ ] Python 3.8+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] SSH key generated and copied to Linux

### Linux (~/audit-system/)
- [ ] `linux_audit.py`
- [ ] `audit_config.json` (configured with your audit commands)
- [ ] Python 3.8+ installed
- [ ] `requests` library installed (`pip3 install requests --user`)
- [ ] SSH public key from Windows in `~/.ssh/authorized_keys`

---

## 🔧 Common Issues & Quick Fixes

### Issue: "Connection refused" when testing tunnel
```bash
curl http://localhost:5000/health
# curl: (7) Failed to connect to localhost port 5000: Connection refused
```

**Fix:**
1. Check Windows Flask service is running
2. Check Windows SSH tunnel is connected
3. On Linux: `ss -tlnp | grep 5000` (should show sshd listening)

### Issue: SSH asks for password
```powershell
ssh your-username@192.168.1.100
# Password: 
```

**Fix:**
```powershell
# Start SSH agent
Get-Service ssh-agent | Set-Service -StartupType Automatic
Start-Service ssh-agent

# Add key
ssh-add $env:USERPROFILE\.ssh\id_ed25519

# Test
ssh your-username@192.168.1.100 "echo Success"
```

### Issue: Screenshot capture fails
```
Screenshot: error ✗
```

**Fix:**
1. Ensure Windows is unlocked (can't capture on lock screen)
2. Test PyAutoGUI: `python -c "import pyautogui; pyautogui.screenshot().save('test.png')"`
3. Check disk space on Windows

### Issue: Python module not found
```
ModuleNotFoundError: No module named 'flask'
```

**Fix:**
```powershell
# On Windows
pip install flask pyautogui pillow
```

```bash
# On Linux
pip3 install requests --user
```

---

## 📝 Customizing Audit Commands

Edit `audit_config.json` on Linux to add your own commands:

```json
{
    "commands": [
        {
            "name": "Your Command Name",
            "command": "your-shell-command-here",
            "description": "What this command checks",
            "critical": true
        }
    ]
}
```

**Examples:**

```json
{
    "name": "Check Docker Containers",
    "command": "docker ps -a",
    "description": "List all Docker containers",
    "critical": false
},
{
    "name": "Check Firewall Rules",
    "command": "sudo iptables -L -n | head -20",
    "description": "Display firewall rules (top 20)",
    "critical": true
},
{
    "name": "Check Apache Status",
    "command": "systemctl status apache2",
    "description": "Verify Apache web server status",
    "critical": true
}
```

---

## 🎓 Tips for Success

### Best Practices

1. **Test connectivity first**
   - Verify SSH connection works manually before running automation
   - Test tunnel with `curl http://localhost:5000/health`

2. **Start small**
   - Begin with 3-5 simple commands
   - Verify everything works before adding more

3. **Review before running**
   - Always check `audit_config.json` before audit
   - Ensure commands are safe (read-only when possible)

4. **Keep screenshots secure**
   - Screenshots may contain sensitive data
   - Delete after audit if not needed for compliance

5. **Version control your configs**
   - Store `audit_config.json` in Git
   - Track changes to audit procedures

### Scheduling Regular Audits

**Windows Task Scheduler:**
```powershell
# Run at 2 AM daily
$action = New-ScheduledTaskAction -Execute "python" -Argument "C:\AuditSystem\windows_start_audit.py"
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "DailyAudit" -Description "Automated audit system"
```

**Linux Cron:**
```bash
# Run at 2:05 AM daily (5 min after Windows starts)
echo "5 2 * * * cd ~/audit-system && python3 linux_audit.py >> ~/audit-cron.log 2>&1" | crontab -
```

---

## 📚 Next Steps

After successful first audit:

1. **Customize commands** - Add your specific audit requirements
2. **Test failure scenarios** - Verify error handling works
3. **Review HTML reports** - Ensure formatting meets your needs
4. **Integrate with existing tools** - Parse JSON logs for automation
5. **Document your process** - Create runbook for team members

---

## 🆘 Getting Help

If you encounter issues:

1. Check the detailed **DEPLOYMENT-GUIDE.md** for comprehensive troubleshooting
2. Review log files:
   - Windows: PowerShell console output
   - Linux: `~/audit-logs/[session-id]/audit_log.txt`
3. Test components individually:
   - Flask service: `curl http://localhost:5000/health`
   - SSH tunnel: `ss -tlnp | grep 5000`
   - Commands: Run manually first

---

**Quick Start Guide Version:** 1.0  
**Total Setup Time:** ~15 minutes  
**Estimated Time to First Audit:** ~20 minutes

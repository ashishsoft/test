# Automated Audit System with SSH Reverse Tunnel

## 🎯 Overview

A fully automated audit system that captures Linux server logs and Windows screenshots for compliance auditing. Uses SSH reverse tunnel to work in enterprise environments **without requiring firewall changes**.

### Key Features

✅ **Fully Automated** - No manual steps during audit execution  
✅ **Firewall-Friendly** - Uses SSH port 22 (already allowed)  
✅ **Enterprise-Ready** - Works in locked-down corporate environments  
✅ **Standardized Audits** - Configuration-driven audit commands  
✅ **Visual Evidence** - Automated screenshot capture  
✅ **Professional Reports** - HTML reports with correlated logs and screenshots  
✅ **Secure** - SSH encryption, no additional open ports  

---

## 📂 Repository Structure

```
audit-system/
├── Windows Components (C:\AuditSystem\)
│   ├── windows_screenshot_service.py    # Flask HTTP server for screenshots
│   ├── windows_start_audit.py           # Automated startup script
│   ├── windows_config.json              # Windows configuration
│   └── requirements.txt                 # Python dependencies
│
├── Linux Components (~/audit-system/)
│   ├── linux_audit.py                   # Main audit execution script
│   └── audit_config.json                # Audit commands configuration
│
└── Documentation
    ├── DEPLOYMENT-GUIDE.md              # Complete deployment guide
    ├── QUICK-START.md                   # 15-minute quick start
    └── README.md                        # This file
```

---

## 🚀 Quick Start

**Total time: 15-20 minutes**

### 1. Windows Setup
```powershell
# Install dependencies
cd C:\
mkdir AuditSystem
cd AuditSystem
pip install flask pyautogui pillow
```

### 2. Linux Setup
```bash
# Install dependencies
mkdir -p ~/audit-system
cd ~/audit-system
pip3 install requests --user
```

### 3. Configure Both Sides
- **Windows:** Edit `windows_config.json` with Linux server details
- **Linux:** Edit `audit_config.json` with audit commands

### 4. Run Audit
```powershell
# On Windows
python windows_start_audit.py
```

```bash
# On Linux
python3 linux_audit.py
```

**👉 See [QUICK-START.md](QUICK-START.md) for detailed step-by-step instructions**

---

## 🏗️ Architecture

### SSH Reverse Tunnel Architecture

```
Windows Machine                        Linux Server
┌──────────────────┐                  ┌──────────────────┐
│ Flask Server     │                  │ Audit Script     │
│ localhost:5000   │◄─────tunnel──────┤ Executes commands│
│                  │                  │ Requests         │
│ Takes screenshot │                  │ screenshots      │
└──────────────────┘                  └──────────────────┘
         │                                      │
         │ SSH Tunnel (Port 22)                 │
         │ Windows → Linux                      │
         └──────────────────────────────────────┘
```

**How It Works:**

1. **Windows initiates** SSH connection to Linux (outbound, always allowed)
2. **SSH tunnel creates** reverse port forwarding (Linux:5000 → Windows:5000)
3. **Linux audit script** sends HTTP requests to its own localhost:5000
4. **SSH daemon forwards** requests through tunnel to Windows
5. **Windows captures** screenshot and returns response through tunnel
6. **Linux logs** everything with perfect timestamp correlation

**Why This Works in Enterprise:**
- Uses standard SSH (port 22) - already approved by IT
- No inbound connections to Windows - no firewall rules needed
- No custom ports - no infrastructure changes required
- Outbound-only from Windows - passes through corporate proxies

---

## 📋 Prerequisites

### Windows
- Windows 10/11 with OpenSSH client (built-in)
- Python 3.8 or higher
- Network access to Linux server (SSH port 22)

### Linux
- Any Linux distribution (Ubuntu, RHEL, CentOS, etc.)
- SSH server running (sshd)
- Python 3.8 or higher
- User account with SSH access

### Network
- Windows can connect to Linux via SSH (port 22)
- No other firewall rules needed!

---

## 🎓 Use Cases

### 1. Compliance Auditing
- SOX, PCI-DSS, ISO27001 compliance checks
- Scheduled daily/weekly/monthly audits
- Automated evidence collection

### 2. Change Management
- Before/after snapshots of system state
- Configuration drift detection
- Service verification after deployments

### 3. Incident Response
- Rapid system state collection
- Evidence preservation with timestamps
- Visual documentation of system status

### 4. Security Audits
- User account verification
- Port scanning and service enumeration
- Permission audits
- Log file analysis

---

## 📊 Sample Output

### Audit Report Includes:

- **Executive Summary**
  - Total commands executed
  - Success/failure statistics
  - Duration and timestamps

- **Detailed Command Results**
  - Command output (stdout/stderr)
  - Exit codes
  - Execution duration
  - Correlated screenshot

- **Visual Evidence**
  - Timestamped screenshots
  - Organized by session
  - Linked to command execution

### Output Formats:

1. **JSON Log** (`audit_log.json`)
   - Machine-readable
   - Easy to parse and integrate
   - Complete audit trail

2. **HTML Report** (`audit_report.html`)
   - Professional formatting
   - Color-coded status
   - Embedded metadata

3. **Text Log** (`audit_log.txt`)
   - Human-readable
   - Easy to review
   - Grep-friendly

4. **Screenshots** (PNG files)
   - Timestamped filenames
   - Organized by session
   - Full resolution

---

## ⚙️ Configuration

### Windows Configuration (`windows_config.json`)

```json
{
    "linux_server": {
        "host": "your-server.example.com",
        "username": "your-username",
        "port": 22
    },
    "screenshot_settings": {
        "local_port": 5000,
        "save_directory": "C:\\AuditScreenshots"
    }
}
```

### Linux Configuration (`audit_config.json`)

```json
{
    "audit_metadata": {
        "auditor_name": "Your Name",
        "environment": "production",
        "compliance_framework": "SOX/ISO27001"
    },
    "commands": [
        {
            "name": "System Hostname",
            "command": "hostname",
            "description": "Verify server identity",
            "critical": true
        }
    ]
}
```

**👉 Add your own audit commands to the `commands` array**

---

## 🔒 Security Considerations

### Best Practices

1. **Use SSH Key Authentication**
   - Generate strong SSH keys
   - Never share private keys
   - Use `ssh-agent` for key management

2. **Audit Command Safety**
   - Use read-only commands when possible
   - Review commands before execution
   - Test in non-production first

3. **Screenshot Protection**
   - May contain sensitive data (passwords, keys)
   - Delete after audit completion if not needed
   - Encrypt if storing long-term

4. **Access Control**
   - Restrict audit script execution to authorized users
   - Use sudo for privileged commands only when necessary
   - Log all audit executions

5. **Network Security**
   - SSH tunnel provides encryption
   - No additional exposed services
   - Audit traffic is fully encrypted

### Compliance Features

- **Audit Trail:** Every command logged with timestamp
- **Non-Repudiation:** Auditor name in metadata
- **Evidence Integrity:** Screenshot correlation with logs
- **Access Logging:** SSH logs track all connections
- **Automation:** Consistent audit process reduces errors

---

## 🔧 Troubleshooting

### Common Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| "Connection refused" on tunnel test | Tunnel not established | Check Windows SSH connection |
| SSH asks for password | SSH key not configured | Run `ssh-keygen` and `ssh-copy-id` |
| Screenshot capture fails | Windows screen locked | Unlock Windows before audit |
| Module not found | Missing Python library | Run `pip install -r requirements.txt` |
| Permission denied on Linux | Insufficient privileges | Use `sudo` for privileged commands |

**👉 See [DEPLOYMENT-GUIDE.md](DEPLOYMENT-GUIDE.md) for comprehensive troubleshooting**

---

## 📚 Documentation

- **[QUICK-START.md](QUICK-START.md)** - 15-minute setup guide
- **[DEPLOYMENT-GUIDE.md](DEPLOYMENT-GUIDE.md)** - Complete deployment documentation

---

## 🎯 Project Goals

This system was designed to solve a specific challenge:

> "How do I automate audit evidence collection (Linux logs + Windows screenshots) in an enterprise environment where I cannot modify firewall rules?"

**Solution:** SSH reverse tunnel architecture
- ✅ No firewall changes
- ✅ Uses approved protocols (SSH)
- ✅ Works through corporate proxies
- ✅ Fully automated
- ✅ Standardized audit procedures

---

## 🛠️ Technology Stack

**Windows Components:**
- Python 3.8+
- Flask (HTTP server)
- PyAutoGUI (screenshot capture)
- Pillow (image processing)
- OpenSSH Client (SSH tunnel)

**Linux Components:**
- Python 3.8+
- Requests (HTTP client)
- Subprocess (command execution)
- JSON (configuration parsing)
- OpenSSH Server (SSH daemon)

**Communication:**
- SSH protocol (port 22)
- HTTP over SSH tunnel
- JSON data exchange

---

## 📈 Extending the System

### Add Custom Commands

Edit `audit_config.json`:
```json
{
    "name": "Your Custom Check",
    "command": "your-command-here",
    "description": "What it checks",
    "critical": true
}
```

### Integrate with External Tools

Parse the JSON log:
```python
import json

with open('audit_log.json') as f:
    data = json.load(f)
    
for result in data['results']:
    print(f"{result['name']}: {result['execution']['exit_code']}")
```

### Schedule Regular Audits

**Windows Task Scheduler:**
```powershell
$action = New-ScheduledTaskAction -Execute "python" -Argument "C:\AuditSystem\windows_start_audit.py"
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "DailyAudit"
```

**Linux Cron:**
```bash
echo "5 2 * * * cd ~/audit-system && python3 linux_audit.py" | crontab -
```

---

## 🤝 Contributing

Suggestions for improvement:
1. Additional output formats (PDF, CSV)
2. Email notifications on audit completion
3. Integration with ticketing systems
4. Multi-server parallel audits
5. Real-time monitoring dashboard

---

## 📝 License

This audit system is provided as-is for enterprise internal use.

---

## 💡 Tips for Success

1. **Start Small:** Begin with 3-5 simple commands
2. **Test First:** Always test in non-production environment
3. **Document Changes:** Version control your `audit_config.json`
4. **Review Reports:** Check HTML reports for formatting
5. **Secure Storage:** Protect audit logs and screenshots
6. **Regular Updates:** Keep Python libraries updated

---

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting sections in documentation
2. Review log files for error messages
3. Test components individually
4. Verify network connectivity
5. Ensure SSH key authentication is working

---

## ✅ Verification Checklist

Before running in production:

- [ ] Windows Python 3.8+ installed and working
- [ ] Linux Python 3.8+ installed and working
- [ ] SSH key authentication configured and tested
- [ ] Windows config file has correct Linux server details
- [ ] Linux config file has correct audit commands
- [ ] Dependencies installed on both systems
- [ ] SSH tunnel can be established manually
- [ ] Test audit completed successfully
- [ ] Screenshot service accessible via tunnel
- [ ] Audit reports generated correctly
- [ ] Screenshots stored in expected location
- [ ] Team trained on running the system

---

**Ready to get started? See [QUICK-START.md](QUICK-START.md) for step-by-step instructions!**

---

**Version:** 1.0  
**Last Updated:** March 6, 2026  
**Architecture:** SSH Reverse Tunnel (Windows → Linux)  
**Status:** Production Ready

#!/usr/bin/env python3
"""
Linux Audit Script
Executes standardized audit commands and captures Windows screenshots via SSH tunnel

This script:
1. Reads audit commands from audit_config.json
2. Executes each command locally on Linux
3. Requests screenshot from Windows via SSH reverse tunnel
4. Logs all results with timestamps
5. Generates audit report

Author: Audit System
Version: 1.0
Date: March 6, 2026
"""

import subprocess
import requests
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Configuration
CONFIG_FILE = "audit_config.json"
SCREENSHOT_SERVICE_URL = "http://localhost:5000"


def load_config():
    """Load audit configuration from JSON file"""
    if not os.path.exists(CONFIG_FILE):
        print(f"ERROR: Configuration file '{CONFIG_FILE}' not found!")
        print(f"Please create {CONFIG_FILE} in the current directory.")
        sys.exit(1)
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {CONFIG_FILE}: {e}")
        sys.exit(1)


def print_header(config):
    """Print audit session header"""
    metadata = config.get('audit_metadata', {})
    
    print("\n" + "="*70)
    print(" "*20 + "AUTOMATED AUDIT SYSTEM")
    print("="*70)
    print(f"Session ID: {config['session_id']}")
    print(f"Auditor: {metadata.get('auditor_name', 'Unknown')}")
    print(f"Environment: {metadata.get('environment', 'Unknown')}")
    print(f"Compliance: {metadata.get('compliance_framework', 'N/A')}")
    print(f"Started: {config['start_time']}")
    print("="*70 + "\n")


def health_check(service_url, timeout=10):
    """Check if screenshot service is accessible"""
    print("[✓] Performing health check on screenshot service...")
    
    try:
        response = requests.get(f"{service_url}/health", timeout=timeout)
        
        if response.status_code == 200:
            data = response.json()
            print(f"    ✓ Screenshot service: {data.get('status', 'unknown').upper()}")
            return True
        else:
            print(f"    ✗ Screenshot service returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("    ✗ Cannot connect to screenshot service!")
        print(f"    Make sure Windows SSH tunnel is established to {service_url}")
        return False
    except requests.exceptions.Timeout:
        print(f"    ✗ Screenshot service timeout after {timeout} seconds")
        return False
    except Exception as e:
        print(f"    ✗ Health check failed: {e}")
        return False


def execute_command(command, timeout=30):
    """
    Execute shell command and capture output
    
    Returns: dict with stdout, stderr, exit_code, duration_ms
    """
    start_time = datetime.now()
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
            "duration_ms": duration_ms,
            "timed_out": False
        }
        
    except subprocess.TimeoutExpired:
        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        return {
            "stdout": "",
            "stderr": f"Command timed out after {timeout} seconds",
            "exit_code": -1,
            "duration_ms": duration_ms,
            "timed_out": True
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "exit_code": -1,
            "duration_ms": 0,
            "timed_out": False
        }


def request_screenshot(service_url, session_id, command, sequence, timeout=10):
    """
    Request screenshot from Windows service via SSH tunnel
    
    Returns: dict with screenshot_id and status
    """
    payload = {
        "session_id": session_id,
        "command": command,
        "sequence": sequence,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(
            f"{service_url}/capture",
            json=payload,
            timeout=timeout
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "status": "error",
                "message": f"HTTP {response.status_code}",
                "screenshot_id": "error"
            }
            
    except requests.exceptions.Timeout:
        return {
            "status": "timeout",
            "message": f"Timeout after {timeout} seconds",
            "screenshot_id": "timeout"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "screenshot_id": "error"
        }


def run_audit(config):
    """Execute audit commands and collect results"""
    commands = config.get('commands', [])
    screenshot_config = config.get('screenshot_service', {})
    service_url = screenshot_config.get('url', SCREENSHOT_SERVICE_URL)
    service_timeout = screenshot_config.get('timeout', 10)
    
    session_id = config['session_id']
    results = []
    
    print("\n" + "-"*70)
    print("Starting audit execution...\n")
    
    for idx, cmd_config in enumerate(commands, 1):
        command = cmd_config.get('command')
        name = cmd_config.get('name', command)
        description = cmd_config.get('description', '')
        critical = cmd_config.get('critical', False)
        
        print(f"[{idx}/{len(commands)}] Executing: {command}")
        
        # Execute command
        exec_result = execute_command(command)
        
        # Display output (truncated if too long)
        stdout_display = exec_result['stdout'].strip()[:200]
        if len(exec_result['stdout']) > 200:
            stdout_display += "..."
        
        print(f"  ├─ Output: {stdout_display if stdout_display else '(empty)'}")
        print(f"  ├─ Exit Code: {exec_result['exit_code']}")
        print(f"  ├─ Duration: {exec_result['duration_ms']}ms")
        
        # Request screenshot
        screenshot_result = request_screenshot(
            service_url,
            session_id,
            command,
            idx,
            service_timeout
        )
        
        screenshot_id = screenshot_result.get('screenshot_id', 'error')
        screenshot_status = "✓" if screenshot_result.get('status') == 'success' else "✗"
        
        print(f"  └─ Screenshot: {screenshot_id} {screenshot_status}")
        print()
        
        # Log result
        result_entry = {
            "sequence": idx,
            "name": name,
            "command": command,
            "description": description,
            "critical": critical,
            "timestamp": datetime.now().isoformat(),
            "execution": exec_result,
            "screenshot": screenshot_result
        }
        
        results.append(result_entry)
        
        # If critical command failed, optionally stop audit
        if critical and exec_result['exit_code'] != 0:
            print(f"⚠️  Critical command failed: {name}")
            # Uncomment to stop on critical failure:
            # break
    
    return results


def save_results(config, results):
    """Save audit results to files"""
    output_options = config.get('output_options', {})
    log_dir = os.path.expanduser(output_options.get('log_directory', '~/audit-logs'))
    session_id = config['session_id']
    
    # Create session directory
    session_dir = os.path.join(log_dir, session_id)
    os.makedirs(session_dir, exist_ok=True)
    
    print("-"*70)
    print("Saving audit results...\n")
    
    # Save JSON log
    if output_options.get('generate_json_log', True):
        json_file = os.path.join(session_dir, 'audit_log.json')
        with open(json_file, 'w') as f:
            audit_data = {
                "session": config,
                "results": results
            }
            json.dump(audit_data, f, indent=2)
        print(f"  ✓ JSON log: {json_file}")
    
    # Save plain text log
    txt_file = os.path.join(session_dir, 'audit_log.txt')
    with open(txt_file, 'w') as f:
        f.write("="*70 + "\n")
        f.write("AUDIT LOG\n")
        f.write("="*70 + "\n\n")
        f.write(f"Session ID: {session_id}\n")
        f.write(f"Start Time: {config['start_time']}\n")
        f.write(f"End Time: {config['end_time']}\n\n")
        
        for result in results:
            f.write("-"*70 + "\n")
            f.write(f"[{result['sequence']}] {result['name']}\n")
            f.write(f"Command: {result['command']}\n")
            f.write(f"Timestamp: {result['timestamp']}\n")
            f.write(f"Exit Code: {result['execution']['exit_code']}\n")
            f.write(f"Duration: {result['execution']['duration_ms']}ms\n")
            f.write(f"Screenshot: {result['screenshot'].get('screenshot_id', 'N/A')}\n")
            f.write(f"\nOutput:\n{result['execution']['stdout']}\n")
            if result['execution']['stderr']:
                f.write(f"\nErrors:\n{result['execution']['stderr']}\n")
            f.write("\n")
    
    print(f"  ✓ Text log: {txt_file}")
    
    # Generate HTML report
    if output_options.get('generate_html_report', True):
        html_file = os.path.join(session_dir, 'audit_report.html')
        generate_html_report(config, results, html_file)
        print(f"  ✓ HTML report: {html_file}")
    
    return session_dir


def generate_html_report(config, results, output_file):
    """Generate HTML audit report"""
    
    # Calculate statistics
    total = len(results)
    successful = sum(1 for r in results if r['execution']['exit_code'] == 0)
    failed = total - successful
    screenshots_captured = sum(1 for r in results if r['screenshot'].get('status') == 'success')
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Audit Report - {config['session_id']}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        .metadata {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .metadata-item {{
            display: inline-block;
            margin-right: 30px;
            margin-bottom: 10px;
        }}
        .metadata-label {{
            font-weight: bold;
            color: #7f8c8d;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-box {{
            background: #3498db;
            color: white;
            padding: 20px;
            border-radius: 5px;
            text-align: center;
        }}
        .stat-box.success {{ background: #27ae60; }}
        .stat-box.error {{ background: #e74c3c; }}
        .stat-box.warning {{ background: #f39c12; }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
        }}
        .command-entry {{
            border: 1px solid #ddd;
            border-radius: 5px;
            margin: 15px 0;
            padding: 15px;
            background: #fafafa;
        }}
        .command-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        .command-name {{
            font-size: 1.2em;
            font-weight: bold;
            color: #2c3e50;
        }}
        .command-status {{
            padding: 5px 15px;
            border-radius: 3px;
            font-size: 0.9em;
            font-weight: bold;
        }}
        .status-success {{
            background: #27ae60;
            color: white;
        }}
        .status-error {{
            background: #e74c3c;
            color: white;
        }}
        .command-details {{
            background: white;
            padding: 10px;
            border-radius: 3px;
            margin: 10px 0;
        }}
        .detail-row {{
            display: flex;
            padding: 5px 0;
            border-bottom: 1px solid #ecf0f1;
        }}
        .detail-label {{
            font-weight: bold;
            width: 150px;
            color: #7f8c8d;
        }}
        .detail-value {{
            flex: 1;
            font-family: 'Courier New', monospace;
        }}
        .output-box {{
            background: #2c3e50;
            color: #ecf0f1;
            padding: 15px;
            border-radius: 3px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .screenshot-info {{
            background: #3498db;
            color: white;
            padding: 10px;
            border-radius: 3px;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Audit Report</h1>
        
        <div class="metadata">
            <div class="metadata-item">
                <span class="metadata-label">Session ID:</span> {config['session_id']}
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Auditor:</span> {config.get('audit_metadata', {}).get('auditor_name', 'N/A')}
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Environment:</span> {config.get('audit_metadata', {}).get('environment', 'N/A')}
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Start Time:</span> {config['start_time']}
            </div>
            <div class="metadata-item">
                <span class="metadata-label">End Time:</span> {config['end_time']}
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Duration:</span> {(datetime.fromisoformat(config['end_time']) - datetime.fromisoformat(config['start_time'])).total_seconds():.2f}s
            </div>
        </div>
        
        <h2>📊 Statistics</h2>
        <div class="stats">
            <div class="stat-box">
                <div class="stat-number">{total}</div>
                <div>Total Commands</div>
            </div>
            <div class="stat-box success">
                <div class="stat-number">{successful}</div>
                <div>Successful</div>
            </div>
            <div class="stat-box error">
                <div class="stat-number">{failed}</div>
                <div>Failed</div>
            </div>
            <div class="stat-box warning">
                <div class="stat-number">{screenshots_captured}</div>
                <div>Screenshots Captured</div>
            </div>
        </div>
        
        <h2>📝 Command Results</h2>
"""
    
    # Add each command result
    for result in results:
        status_class = "status-success" if result['execution']['exit_code'] == 0 else "status-error"
        status_text = "SUCCESS" if result['execution']['exit_code'] == 0 else "FAILED"
        
        html_content += f"""
        <div class="command-entry">
            <div class="command-header">
                <div class="command-name">[{result['sequence']}] {result['name']}</div>
                <div class="command-status {status_class}">{status_text}</div>
            </div>
            
            <div class="command-details">
                <div class="detail-row">
                    <div class="detail-label">Command:</div>
                    <div class="detail-value">{result['command']}</div>
                </div>
                <div class="detail-row">
                    <div class="detail-label">Description:</div>
                    <div class="detail-value">{result.get('description', 'N/A')}</div>
                </div>
                <div class="detail-row">
                    <div class="detail-label">Timestamp:</div>
                    <div class="detail-value">{result['timestamp']}</div>
                </div>
                <div class="detail-row">
                    <div class="detail-label">Exit Code:</div>
                    <div class="detail-value">{result['execution']['exit_code']}</div>
                </div>
                <div class="detail-row">
                    <div class="detail-label">Duration:</div>
                    <div class="detail-value">{result['execution']['duration_ms']}ms</div>
                </div>
            </div>
            
            <h4>Output:</h4>
            <div class="output-box">{result['execution']['stdout'] if result['execution']['stdout'] else '(no output)'}</div>
            
            {f'<div class="output-box" style="background: #c0392b; margin-top: 10px;">ERROR: {result["execution"]["stderr"]}</div>' if result['execution']['stderr'] else ''}
            
            <div class="screenshot-info">
                📷 Screenshot: {result['screenshot'].get('screenshot_id', 'N/A')} 
                (Status: {result['screenshot'].get('status', 'unknown')})
                <br>
                <small>Location: Windows machine at C:\\AuditScreenshots\\{config['session_id']}\\</small>
            </div>
        </div>
"""
    
    html_content += """
    </div>
</body>
</html>
"""
    
    with open(output_file, 'w') as f:
        f.write(html_content)


def print_summary(config, results, session_dir):
    """Print audit summary"""
    total = len(results)
    successful = sum(1 for r in results if r['execution']['exit_code'] == 0)
    failed = total - successful
    
    duration = (datetime.fromisoformat(config['end_time']) - 
                datetime.fromisoformat(config['start_time'])).total_seconds()
    
    print("\n" + "="*70)
    print("Audit completed successfully!")
    print("="*70)
    print(f"Total commands: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total duration: {duration:.1f} seconds")
    print()
    print("Results saved to:")
    print(f"  📄 Log: {session_dir}/audit_log.json")
    print(f"  📄 Log: {session_dir}/audit_log.txt")
    print(f"  📊 Report: {session_dir}/audit_report.html")
    print(f"  📷 Screenshots: On Windows at C:\\AuditScreenshots\\{config['session_id']}\\")
    print("="*70 + "\n")


def main():
    """Main entry point"""
    # Load configuration
    config = load_config()
    
    # Add session metadata
    session_id = f"audit-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    start_time = datetime.now().isoformat()
    
    config['session_id'] = session_id
    config['start_time'] = start_time
    
    # Print header
    print_header(config)
    
    # Health check
    screenshot_config = config.get('screenshot_service', {})
    service_url = screenshot_config.get('url', SCREENSHOT_SERVICE_URL)
    
    if not health_check(service_url, screenshot_config.get('timeout', 10)):
        print("\n⚠️  Screenshot service is not available!")
        print("Options:")
        print("  1. Continue without screenshots (press Enter)")
        print("  2. Exit and fix the issue (press Ctrl+C)")
        
        try:
            input()
            print("Continuing without screenshot service...\n")
        except KeyboardInterrupt:
            print("\n\nAudit cancelled.")
            sys.exit(0)
    
    print()
    
    # Run audit
    results = run_audit(config)
    
    # Add end time
    config['end_time'] = datetime.now().isoformat()
    
    # Save results
    session_dir = save_results(config, results)
    
    # Print summary
    print_summary(config, results, session_dir)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAudit interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

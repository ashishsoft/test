"""
Windows Audit System Launcher
Automated startup script that:
1. Starts Flask screenshot service
2. Establishes SSH reverse tunnel to Linux server
3. Monitors both processes
4. Provides status dashboard

Author: Audit System
Version: 1.0
Date: March 6, 2026
"""

import subprocess
import time
import json
import os
import sys
import signal
from datetime import datetime

# Configuration
CONFIG_FILE = "windows_config.json"

# Process handles
flask_process = None
ssh_process = None


def load_config():
    """Load configuration from JSON file"""
    if not os.path.exists(CONFIG_FILE):
        print(f"ERROR: Configuration file '{CONFIG_FILE}' not found!")
        print(f"Please create {CONFIG_FILE} with your Linux server details.")
        sys.exit(1)
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {CONFIG_FILE}: {e}")
        sys.exit(1)


def print_header():
    """Print application header"""
    print("\n" + "="*70)
    print(" "*15 + "AUTOMATED AUDIT SYSTEM")
    print(" "*10 + "Windows Component - SSH Reverse Tunnel")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")


def start_flask_service(port=5000):
    """Start Flask screenshot service"""
    global flask_process
    
    print("[1/2] Starting Flask screenshot service...")
    
    try:
        flask_process = subprocess.Popen(
            [sys.executable, "windows_screenshot_service.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Wait a moment for Flask to start
        time.sleep(3)
        
        # Check if process is still running
        if flask_process.poll() is not None:
            print("      ✗ Flask service failed to start!")
            return False
        
        print(f"      ✓ Flask service running (PID: {flask_process.pid})")
        print(f"      ✓ Listening on: http://localhost:{port}")
        return True
        
    except Exception as e:
        print(f"      ✗ Error starting Flask: {e}")
        return False


def establish_ssh_tunnel(config):
    """Establish SSH reverse tunnel to Linux server"""
    global ssh_process
    
    print("\n[2/2] Establishing SSH reverse tunnel...")
    
    # Extract configuration
    linux_config = config.get('linux_server', {})
    host = linux_config.get('host')
    username = linux_config.get('username')
    port = linux_config.get('port', 22)
    
    screenshot_config = config.get('screenshot_settings', {})
    local_port = screenshot_config.get('local_port', 5000)
    
    if not host or not username:
        print("      ✗ Missing Linux server configuration!")
        print("      Please configure 'linux_server' in windows_config.json")
        return False
    
    print(f"      Target: {username}@{host}:{port}")
    print(f"      Tunnel: Linux:{local_port} → Windows:localhost:{local_port}")
    
    # Build SSH command
    # -R: Reverse tunnel (remote port forwarding)
    # -N: Don't execute remote command (just tunnel)
    # -o ServerAliveInterval=60: Send keepalive every 60 seconds
    # -o ServerAliveCountMax=3: Disconnect after 3 failed keepalives
    ssh_cmd = [
        'ssh',
        '-R', f'{local_port}:localhost:{local_port}',
        '-N',  # No command execution
        '-o', 'ServerAliveInterval=60',
        '-o', 'ServerAliveCountMax=3',
        '-o', 'ExitOnForwardFailure=yes',
        '-p', str(port),
        f'{username}@{host}'
    ]
    
    try:
        ssh_process = subprocess.Popen(
            ssh_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment for SSH to connect
        time.sleep(5)
        
        # Check if process is still running
        if ssh_process.poll() is not None:
            stderr = ssh_process.stderr.read()
            print("      ✗ SSH tunnel failed to establish!")
            if stderr:
                print(f"      Error: {stderr}")
            return False
        
        print(f"      ✓ SSH tunnel established (PID: {ssh_process.pid})")
        print(f"      ✓ Linux server can access: http://localhost:{local_port}")
        return True
        
    except FileNotFoundError:
        print("      ✗ SSH client not found!")
        print("      Please ensure OpenSSH client is installed on Windows.")
        return False
    except Exception as e:
        print(f"      ✗ Error establishing tunnel: {e}")
        return False


def print_status_dashboard(config):
    """Print status dashboard"""
    print("\n" + "="*70)
    print(" "*20 + "SYSTEM STATUS")
    print("="*70)
    
    linux_config = config.get('linux_server', {})
    screenshot_config = config.get('screenshot_settings', {})
    
    # Component status
    print("\n📊 Components:")
    print(f"   Flask Service:     {'🟢 Running' if flask_process and flask_process.poll() is None else '🔴 Stopped'}")
    print(f"   SSH Tunnel:        {'🟢 Connected' if ssh_process and ssh_process.poll() is None else '🔴 Disconnected'}")
    
    # Configuration
    print("\n⚙️  Configuration:")
    print(f"   Linux Server:      {linux_config.get('username')}@{linux_config.get('host')}")
    print(f"   Screenshot Dir:    {screenshot_config.get('save_directory', 'C:\\AuditScreenshots')}")
    print(f"   Local Port:        {screenshot_config.get('local_port', 5000)}")
    
    # Instructions
    print("\n📝 Next Steps:")
    print("   1. SSH to your Linux server")
    print("   2. Verify tunnel: curl http://localhost:5000/health")
    print("   3. Run audit: python3 linux_audit.py")
    print("   4. Press Ctrl+C here when done to stop services")
    
    print("\n" + "="*70)
    print(" "*15 + "System ready for audit execution")
    print("="*70 + "\n")


def cleanup():
    """Cleanup processes on exit"""
    global flask_process, ssh_process
    
    print("\n\nShutting down services...")
    
    if flask_process and flask_process.poll() is None:
        print("   Stopping Flask service...")
        flask_process.terminate()
        try:
            flask_process.wait(timeout=5)
            print("   ✓ Flask service stopped")
        except subprocess.TimeoutExpired:
            flask_process.kill()
            print("   ✓ Flask service killed")
    
    if ssh_process and ssh_process.poll() is None:
        print("   Closing SSH tunnel...")
        ssh_process.terminate()
        try:
            ssh_process.wait(timeout=5)
            print("   ✓ SSH tunnel closed")
        except subprocess.TimeoutExpired:
            ssh_process.kill()
            print("   ✓ SSH tunnel killed")
    
    print("\n✓ All services stopped")
    print("Goodbye!\n")


def monitor_processes():
    """Monitor processes and restart if needed"""
    print("Monitoring services (press Ctrl+C to stop)...\n")
    
    check_interval = 10  # Check every 10 seconds
    
    try:
        while True:
            time.sleep(check_interval)
            
            # Check Flask service
            if flask_process and flask_process.poll() is not None:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  Flask service stopped unexpectedly!")
                break
            
            # Check SSH tunnel
            if ssh_process and ssh_process.poll() is not None:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  SSH tunnel disconnected!")
                break
            
            # Print heartbeat every minute
            current_time = datetime.now()
            if current_time.second < check_interval:
                print(f"[{current_time.strftime('%H:%M:%S')}] ✓ Services running normally...")
    
    except KeyboardInterrupt:
        print("\n\nReceived shutdown signal...")


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    cleanup()
    sys.exit(0)


def main():
    """Main entry point"""
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Print header
    print_header()
    
    # Load configuration
    print("Loading configuration...")
    config = load_config()
    print("✓ Configuration loaded\n")
    
    # Start Flask service
    if not start_flask_service(config.get('screenshot_settings', {}).get('local_port', 5000)):
        print("\nFailed to start Flask service. Exiting...")
        sys.exit(1)
    
    # Establish SSH tunnel
    if not establish_ssh_tunnel(config):
        print("\nFailed to establish SSH tunnel. Stopping services...")
        cleanup()
        sys.exit(1)
    
    # Print status dashboard
    print_status_dashboard(config)
    
    # Monitor processes
    monitor_processes()
    
    # Cleanup on exit
    cleanup()


if __name__ == '__main__':
    main()

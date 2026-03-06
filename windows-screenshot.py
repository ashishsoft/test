"""
Windows Screenshot Service
Flask HTTP server that captures screenshots on demand

This service runs on Windows localhost and is accessed via SSH reverse tunnel
from the Linux audit script.

Author: Audit System
Version: 1.0
Date: March 6, 2026
"""

from flask import Flask, request, jsonify
import pyautogui
import os
import datetime
import json
import sys
from pathlib import Path

# Initialize Flask app
app = Flask(__name__)

# Configuration
CONFIG_FILE = "windows_config.json"
DEFAULT_SCREENSHOT_DIR = "C:\\AuditScreenshots"
DEFAULT_PORT = 5000


def load_config():
    """Load configuration from JSON file"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get('screenshot_settings', {})
        return {}
    except Exception as e:
        print(f"Warning: Could not load config file: {e}")
        return {}


# Load settings
settings = load_config()
SCREENSHOT_DIR = settings.get('save_directory', DEFAULT_SCREENSHOT_DIR)
PORT = settings.get('local_port', DEFAULT_PORT)

# Ensure screenshot directory exists
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

print("="*60)
print("  WINDOWS SCREENSHOT SERVICE")
print("="*60)
print(f"Screenshot Directory: {SCREENSHOT_DIR}")
print(f"Listening Port: {PORT}")
print(f"Service URL: http://localhost:{PORT}")
print("="*60)
print()


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    Returns: JSON with status and timestamp
    """
    return jsonify({
        "status": "ok",
        "service": "Windows Screenshot Service",
        "timestamp": datetime.datetime.now().isoformat(),
        "screenshot_directory": SCREENSHOT_DIR
    })


@app.route('/capture', methods=['POST'])
def capture_screenshot():
    """
    Capture screenshot endpoint
    
    Expected POST body:
    {
        "session_id": "audit-20260306-174230",
        "command": "hostname",
        "sequence": 1,
        "timestamp": "2026-03-06T17:42:30.123456"
    }
    
    Returns: JSON with screenshot details
    """
    try:
        # Parse request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "No JSON data provided"
            }), 400
        
        # Extract metadata
        session_id = data.get('session_id', 'unknown-session')
        command = data.get('command', 'unknown-command')
        sequence = data.get('sequence', 0)
        timestamp = data.get('timestamp', datetime.datetime.now().isoformat())
        
        # Create session directory
        session_dir = os.path.join(SCREENSHOT_DIR, session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        # Generate filename
        # Format: 001_hostname_20260306-174230.png
        clean_command = command.replace(' ', '-').replace('/', '-')[:30]  # Sanitize command name
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{sequence:03d}_{clean_command}_{timestamp_str}.png"
        filepath = os.path.join(session_dir, filename)
        
        # Capture screenshot
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Capturing screenshot: {filename}")
        screenshot = pyautogui.screenshot()
        
        # Save screenshot
        screenshot.save(filepath, format='PNG', optimize=True)
        
        # Get file size for response
        file_size = os.path.getsize(filepath)
        
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ✓ Screenshot saved: {filepath} ({file_size} bytes)")
        
        # Return success response
        return jsonify({
            "status": "success",
            "screenshot_id": filename,
            "filepath": filepath,
            "file_size_bytes": file_size,
            "capture_timestamp": datetime.datetime.now().isoformat(),
            "metadata": {
                "session_id": session_id,
                "command": command,
                "sequence": sequence
            }
        })
        
    except Exception as e:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ✗ Screenshot capture failed: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__
        }), 500


@app.route('/info', methods=['GET'])
def service_info():
    """
    Service information endpoint
    Returns: Service details and statistics
    """
    # Count total sessions and screenshots
    total_sessions = 0
    total_screenshots = 0
    
    if os.path.exists(SCREENSHOT_DIR):
        sessions = [d for d in os.listdir(SCREENSHOT_DIR) if os.path.isdir(os.path.join(SCREENSHOT_DIR, d))]
        total_sessions = len(sessions)
        
        for session in sessions:
            session_path = os.path.join(SCREENSHOT_DIR, session)
            screenshots = [f for f in os.listdir(session_path) if f.endswith('.png')]
            total_screenshots += len(screenshots)
    
    return jsonify({
        "service": "Windows Screenshot Service",
        "version": "1.0",
        "status": "running",
        "port": PORT,
        "screenshot_directory": SCREENSHOT_DIR,
        "statistics": {
            "total_sessions": total_sessions,
            "total_screenshots": total_screenshots
        },
        "endpoints": {
            "health": "/health",
            "capture": "/capture (POST)",
            "info": "/info"
        }
    })


def run_server():
    """Start the Flask server"""
    print("Starting Flask server...")
    print("Press Ctrl+C to stop")
    print()
    
    # Run on localhost only (no external access = no firewall rules needed)
    # This is accessed via SSH reverse tunnel
    app.run(
        host='127.0.0.1',  # Localhost only
        port=PORT,
        debug=False,
        use_reloader=False  # Disable reloader to avoid double startup
    )


if __name__ == '__main__':
    try:
        run_server()
    except KeyboardInterrupt:
        print("\n\nShutting down screenshot service...")
        print("Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        sys.exit(1)

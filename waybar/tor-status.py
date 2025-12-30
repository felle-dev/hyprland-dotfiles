#!/usr/bin/env python3
import json
import subprocess
import urllib.request
import urllib.error
import os
import sys
from pathlib import Path

# State file to track previous status
STATE_FILE = Path.home() / '.cache' / 'tor_status_state.json'

def disable_proxy():
    """Disable system proxy settings and iptables rules for Hyprland"""
    try:
        # Path to proxy config file
        proxy_config = Path.home() / '.config' / 'environment.d' / 'proxy.conf'
        
        # Remove proxy config file
        if proxy_config.exists():
            proxy_config.unlink()
        
        # Remove specific Tor iptables rules without flushing everything
        tor_rules = [
            # Remove TCP redirect to 9040
            ['sudo', 'iptables', '-t', 'nat', '-D', 'OUTPUT', '-p', 'tcp', '--syn', '-j', 'REDIRECT', '--to-ports', '9040'],
            # Remove DNS redirects to 5353
            ['sudo', 'iptables', '-t', 'nat', '-D', 'OUTPUT', '-p', 'udp', '--dport', '53', '-j', 'REDIRECT', '--to-ports', '5353'],
            ['sudo', 'iptables', '-t', 'nat', '-D', 'OUTPUT', '-p', 'tcp', '--dport', '53', '-j', 'REDIRECT', '--to-ports', '5353'],
        ]
        
        for rule in tor_rules:
            try:
                subprocess.run(rule, capture_output=True, timeout=3)
            except:
                pass
        
        # Clear Firefox proxy (if using Firefox)
        try:
            subprocess.run(
                ['pkill', '-SIGUSR1', 'firefox'],
                capture_output=True,
                timeout=2
            )
        except:
            pass
        
        # Clear Chromium/Chrome proxy via command line flags file
        chrome_flags = Path.home() / '.config' / 'chromium-flags.conf'
        if chrome_flags.exists():
            with open(chrome_flags, 'r') as f:
                lines = f.readlines()
            new_lines = [line for line in lines if '--proxy-server' not in line]
            with open(chrome_flags, 'w') as f:
                f.writelines(new_lines)
        
        # Clear Brave proxy
        brave_flags = Path.home() / '.config' / 'brave-flags.conf'
        if brave_flags.exists():
            with open(brave_flags, 'r') as f:
                lines = f.readlines()
            new_lines = [line for line in lines if '--proxy-server' not in line]
            with open(brave_flags, 'w') as f:
                f.writelines(new_lines)
        
        return True
    except Exception as e:
        return False

def enable_proxy():
    """Enable system proxy settings for Hyprland"""
    try:
        # Create environment.d directory if it doesn't exist
        env_dir = Path.home() / '.config' / 'environment.d'
        env_dir.mkdir(parents=True, exist_ok=True)
        
        # Write proxy configuration
        proxy_config = env_dir / 'proxy.conf'
        with open(proxy_config, 'w') as f:
            f.write('# Tor SOCKS5 Proxy\n')
            f.write('http_proxy=socks5://127.0.0.1:9050\n')
            f.write('https_proxy=socks5://127.0.0.1:9050\n')
            f.write('HTTP_PROXY=socks5://127.0.0.1:9050\n')
            f.write('HTTPS_PROXY=socks5://127.0.0.1:9050\n')
            f.write('all_proxy=socks5://127.0.0.1:9050\n')
            f.write('ALL_PROXY=socks5://127.0.0.1:9050\n')
        
        # Add Tor iptables rules
        tor_rules = [
            # Redirect TCP to transparent proxy on 9040
            ['sudo', 'iptables', '-t', 'nat', '-A', 'OUTPUT', '-p', 'tcp', '--syn', '-j', 'REDIRECT', '--to-ports', '9040'],
            # Redirect DNS to 5353
            ['sudo', 'iptables', '-t', 'nat', '-A', 'OUTPUT', '-p', 'udp', '--dport', '53', '-j', 'REDIRECT', '--to-ports', '5353'],
            ['sudo', 'iptables', '-t', 'nat', '-A', 'OUTPUT', '-p', 'tcp', '--dport', '53', '-j', 'REDIRECT', '--to-ports', '5353'],
        ]
        
        for rule in tor_rules:
            try:
                subprocess.run(rule, capture_output=True, timeout=3)
            except:
                pass
        
        return True
    except Exception as e:
        return False

def toggle_tor_service():
    """Toggle Tor service on/off with proxy management"""
    try:
        # Check current status
        result = subprocess.run(
            ['systemctl', 'is-active', 'tor'],
            capture_output=True,
            text=True,
            timeout=2
        )
        is_active = result.stdout.strip() == 'active'
        
        if is_active:
            # Stop Tor and disable proxy
            subprocess.run(['sudo', 'systemctl', 'stop', 'tor'], timeout=5, check=True)
            if disable_proxy():
                subprocess.run(
                    ['notify-send', '-t', '3000', '-u', 'normal', '🔓 Tor Disabled', 'Proxy settings removed'],
                    capture_output=True
                )
        else:
            # Start Tor and enable proxy
            subprocess.run(['sudo', 'systemctl', 'start', 'tor'], timeout=5, check=True)
            if enable_proxy():
                subprocess.run(
                    ['notify-send', '-t', '3000', '-u', 'normal', '🔒 Tor Enabled', 'Proxy configured - restart apps to apply'],
                    capture_output=True
                )
    except Exception as e:
        subprocess.run(
            ['notify-send', '-t', '3000', '-u', 'critical', '❌ Tor Toggle Failed', str(e)],
            capture_output=True
        )

# Handle click events
if len(sys.argv) > 1 and sys.argv[1] == 'toggle':
    toggle_tor_service()
    sys.exit(0)

def load_previous_state():
    """Load previous state from file"""
    try:
        if STATE_FILE.exists():
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {'status': None, 'bootstrap': 0, 'proxy_notified': False}

def save_state(status, bootstrap, proxy_notified=False):
    """Save current state to file"""
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, 'w') as f:
            json.dump({'status': status, 'bootstrap': bootstrap, 'proxy_notified': proxy_notified}, f)
    except:
        pass

def check_tor_service():
    """Check if Tor service is running"""
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', 'tor'],
            capture_output=True,
            text=True,
            timeout=2
        )
        return result.stdout.strip() == 'active'
    except:
        return False

def check_tor_connection():
    """Check if actually connected through Tor network"""
    try:
        req = urllib.request.Request(
            'https://check.torproject.org/api/ip',
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            return data.get('IsTor', False)
    except:
        return False

def check_bootstrap():
    """Check Tor bootstrap status"""
    try:
        result = subprocess.run(
            ['journalctl', '-u', 'tor', '-n', '50', '--no-pager'],
            capture_output=True,
            text=True,
            timeout=2
        )
        lines = result.stdout.strip().split('\n')
        
        for line in reversed(lines):
            if 'Bootstrapped 100%' in line:
                return 100
            elif 'Bootstrapped' in line:
                try:
                    percent = line.split('Bootstrapped ')[1].split('%')[0]
                    return int(percent)
                except:
                    pass
        return 0
    except:
        return 0

def check_proxy_exists():
    """Check if proxy config file exists"""
    proxy_config = Path.home() / '.config' / 'environment.d' / 'proxy.conf'
    return proxy_config.exists()

# Load previous state
prev_state = load_previous_state()

# Check Tor status
tor_service = check_tor_service()
bootstrap_percent = check_bootstrap() if tor_service else 0
tor_connected = check_tor_connection() if bootstrap_percent == 100 else False
proxy_exists = check_proxy_exists()

# Manage proxy state - only disable if status changed
if not tor_service and proxy_exists:
    # Tor is off but proxy still exists - remove it silently
    disable_proxy()
    proxy_notified = True
elif tor_service and not proxy_exists and bootstrap_percent == 100:
    # Tor is fully running but proxy doesn't exist - create it silently
    enable_proxy()
    proxy_notified = True
else:
    proxy_notified = prev_state.get('proxy_notified', False)

# Determine status
if tor_connected:
    icon = ""
    text = "TOR"
    status_class = "tor-active"
    tooltip = "🔒 Tor network is active\n✅ Your traffic is anonymized\n🌐 Proxy enabled"
    current_status = "connected"
elif tor_service and bootstrap_percent > 0:
    icon = ""
    text = f"{bootstrap_percent}%"
    status_class = "tor-connecting"
    tooltip = f"🔄 Tor is connecting...\n📊 Bootstrap: {bootstrap_percent}%"
    current_status = "connecting"
elif tor_service:
    icon = "󰔟"
    text = "START"
    status_class = "tor-starting"
    tooltip = "⏳ Tor service is starting..."
    current_status = "starting"
else:
    icon = "󱎛"
    text = "OFF"
    status_class = "tor-off"
    tooltip = "🔓 Tor is not running\n🖱️ Click to start\n🌐 Direct connection"
    current_status = "off"

# Save current state
save_state(current_status, bootstrap_percent, proxy_notified)

# Format output
output = {
    "text": f"{icon} {text}",
    "tooltip": tooltip,
    "class": status_class,
    "percentage": bootstrap_percent
}

print(json.dumps(output))

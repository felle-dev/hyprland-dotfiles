#!/bin/bash
# =============================================================
# VPN Status Script for Waybar
# =============================================================

CURRENT_FILE="/tmp/protonvpn-current"

# Country name mapping
get_country_name() {
    case "$1" in
        ca) echo "Canada" ;;
        jp) echo "Japan" ;;
        no) echo "Norway" ;;
        mx) echo "Mexico" ;;
        nl) echo "Belanda" ;;
        pl) echo "Polandia" ;;
        ro) echo "Romania" ;;
        sg) echo "Singapura" ;;
        ch) echo "Swiss" ;;
        *) echo "VPN" ;;
    esac
}

# Check if VPN is running
if systemctl is-active --quiet "openvpn-client@*"; then
    if [ -f "$CURRENT_FILE" ]; then
        CONFIG=$(cat "$CURRENT_FILE")
        COUNTRY_CODE=$(echo "$CONFIG" | cut -d'-' -f1)
        COUNTRY_NAME=$(get_country_name "$COUNTRY_CODE")
        echo "{\"text\":\"$COUNTRY_NAME\",\"tooltip\":\"VPN Connected: $CONFIG\",\"class\":\"connected\"}"
    else
        echo "{\"text\":\" Connected\",\"tooltip\":\"VPN Connected\",\"class\":\"connected\"}"
    fi
else
    echo "{\"text\":\"󰷷\",\"tooltip\":\"VPN Disconnected - Click to connect\",\"class\":\"disconnected\"}"
fi

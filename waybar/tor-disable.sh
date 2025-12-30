#!/bin/bash

# Script to remove iptables redirect rules and test connection
# Make sure to run this script with sudo privileges

echo "Removing iptables redirect rules..."

# Remove the redirect rules
sudo iptables -t nat -D OUTPUT -p tcp --syn -j REDIRECT --to-ports 9040
sudo iptables -t nat -D OUTPUT -p udp --dport 53 -j REDIRECT --to-ports 5353
sudo iptables -t nat -D OUTPUT -p tcp --dport 53 -j REDIRECT --to-ports 5353

echo "Redirect rules removed."
echo ""
echo "Testing connection to Google..."

# Test if it works
curl https://google.com

echo ""
echo "Test complete."

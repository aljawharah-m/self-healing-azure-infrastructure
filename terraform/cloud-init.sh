#!/bin/bash
apt-get update -y
apt-get install -y nginx stress-ng
systemctl enable nginx
systemctl start nginx
echo "Self-Healing Network Node - Healthy" > /var/www/html/index.html
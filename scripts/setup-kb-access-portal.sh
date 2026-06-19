#!/usr/bin/env bash
# One-time deploy: kb-access.waytie.com portal (DNS, nginx, certbot, systemd).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SECRET="/mnt/blockstorage/private/credentials/kb-access-approve-secret.txt"
DATA="/mnt/blockstorage/private/kb-access-requests"

if [[ ! -f "$SECRET" ]]; then
  openssl rand -hex 32 > "$SECRET"
  chmod 600 "$SECRET"
  echo "created $SECRET"
fi

mkdir -p "$DATA"
chmod 700 "$DATA"

# DNS via Namecheap (same pattern as kb-mcp)
python3 <<'PY'
import urllib.parse, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path
user = Path("/mnt/blockstorage/private/credentials/namecheap-api-username.txt").read_text().strip()
key = Path("/mnt/blockstorage/private/credentials/namecheap-api-token.txt").read_text().strip()
client_ip = "192.241.169.31"
SERVER = "192.241.169.31"
NEW = "kb-access"

def api(cmd, extra=None):
    p = {"ApiUser": user, "ApiKey": key, "UserName": user, "ClientIp": client_ip,
         "Command": cmd, "SLD": "waytie", "TLD": "com"}
    if extra: p.update(extra)
    with urllib.request.urlopen("https://api.namecheap.com/xml.response?" + urllib.parse.urlencode(p)) as r:
        return r.read()

root = ET.fromstring(api("namecheap.domains.dns.getHosts"))
ns = {"nc": "http://api.namecheap.com/xml.response"}
hosts = []
for h in root.findall(".//nc:DomainDNSGetHostsResult/nc:host", ns):
    hosts.append({"Name": h.get("Name"), "Type": h.get("Type"), "Address": h.get("Address"), "TTL": h.get("TTL") or "1800"})
if any(h["Name"] == NEW for h in hosts):
    print("DNS kb-access already present")
else:
    hosts.append({"Name": NEW, "Type": "A", "Address": SERVER, "TTL": "1800"})
    extra = {}
    for i, h in enumerate(hosts, 1):
        extra[f"HostName{i}"] = h["Name"]
        extra[f"RecordType{i}"] = h["Type"]
        extra[f"Address{i}"] = h["Address"]
        extra[f"TTL{i}"] = h["TTL"]
    api("namecheap.domains.dns.setHosts", extra)
    print("DNS kb-access added")
PY

sudo cp "$ROOT/deploy/nginx-kb-access-waytie.conf" /etc/nginx/sites-available/kb-access.waytie.com
sudo ln -sf /etc/nginx/sites-available/kb-access.waytie.com /etc/nginx/sites-enabled/kb-access.waytie.com
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d kb-access.waytie.com --non-interactive --agree-tos --register-unsafely-without-email --redirect 2>&1 | tail -5

sudo cp "$ROOT/deploy/kb-access.service" /etc/systemd/system/kb-access.service
sudo systemctl daemon-reload
sudo systemctl enable --now kb-access.service
systemctl is-active kb-access.service

echo "Portal: https://kb-access.waytie.com"

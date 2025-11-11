#!/usr/bin/env python3
import hmac
import hashlib
import base64
import json
import time
import requests
import psutil
import ipaddress
import sys

from config import *

def is_ipv4_public(addr: str) -> bool:
    try:
        ip = ipaddress.IPv4Address(addr)
        return ip.is_global
    except Exception:
        return False

def is_ipv6_public(addr: str) -> bool:
    try:
        ip = ipaddress.IPv6Address(addr)
        return ip.is_global
    except Exception:
        return False

def obtain_public_ip(ipv6=False):
    family = "IPv6" if ipv6 else "IPv4"
    print(f"retrieving public {family} address...")

    # first, try remote URL if defined
    url = CF_IPV6_UPDATE_URL if ipv6 else CF_IPV4_UPDATE_URL
    if url:
        try:
            # for icanhazip only
            resp = requests.get(url, timeout=5).text.strip("\n")

            if ipv6:
                ip_is_public = is_ipv6_public(resp)
            else:
                ip_is_public = is_ipv4_public(resp)
                
            if ip_is_public:
                return resp
        except Exception as e:
            print(f"remote {family} lookup failed: {e}")

    # fallback: scan local interfaces
    for nic, addrs in psutil.net_if_addrs().items():
        for a in addrs:
            if ipv6 and a.family.name == "AF_INET6" and is_ipv6_public(a.address):
                return a.address.split("%")[0]
            if not ipv6 and a.family.name == "AF_INET" and is_ipv4_public(a.address):
                return a.address
    raise RuntimeError(f"no public {family} address found")

def hmac_sign(token, message):
    digest = hmac.new(token.encode(), message.encode(), hashlib.sha256).digest()
    return base64.b64encode(digest).decode()

def cf_update(ipv6=False):
    addr_family = "IPv6" if ipv6 else "IPv4"
    try:
        ip = obtain_public_ip(ipv6)
        print(f"got {addr_family} address: {ip}")
        payload = {
            "id": CF_TOKEN_ID,
            "domain": CF_DOMAIN,
            "type": addr_family.lower(),
            "addr": ip,
            "timestamp": int(time.time()) - 60,
        }
        body = json.dumps(payload, separators=(",", ":"))
        sign = hmac_sign(CF_TOKEN, body)
        headers = {"Authorization": sign, "Content-Type": "application/json"}
        resp = requests.post(CF_WORKER_URL, headers=headers, data=body)
        resp.raise_for_status()
        print("success!")
    except Exception as e:
        print(f"failed: {e}")

def main():
    if CF_IPV4_ENABLED:
        cf_update(False)
    if CF_IPV6_ENABLED:
        cf_update(True)

if __name__ == "__main__":
    main()

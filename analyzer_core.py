"""Clean analyzer implementation used by the app and tests.

This module contains a minimal, well-formed implementation so it can be
imported reliably even if other files are corrupted during editing.
"""
from ipaddress import IPv4Address, IPv4Network
from typing import List, Dict, Any, Tuple


def parse_interfaces(text: str) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
    if not text:
        return items
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        items.append({"name": parts[0], "ip": parts[1], "raw": line})
    return items


def analyze_options(options: Dict[str, Any]) -> Dict[str, Any]:
    issues: List[str] = []
    recs: List[Tuple[str, str]] = []

    interfaces_text = options.get("interfaces") or ""
    bgp_asn = (options.get("bgp_asn") or "").strip()

    ints = parse_interfaces(interfaces_text)

    seen_ips: Dict[str, str] = {}
    for it in ints:
        name = it.get("name", "<unknown>")
        ipraw = it.get("ip", "")
        if not ipraw:
            issues.append(f"Missing IP on {name}")
            continue
        if '/' in ipraw:
            try:
                net = IPv4Network(ipraw, strict=False)
                ip_key = f"{net.network_address}/{net.prefixlen}"
            except Exception:
                issues.append(f"Invalid network/ip: '{ipraw}' on {name}")
                continue
        else:
            try:
                addr = IPv4Address(ipraw)
                ip_key = str(addr)
            except Exception:
                issues.append(f"Invalid IP: '{ipraw}' on {name}")
                continue

        if ip_key in seen_ips:
            issues.append(f"Duplicate IP {ipraw} found on {name} and {seen_ips[ip_key]}")
        else:
            seen_ips[ip_key] = name

    # Recommend loopback if none present
    has_loopback = any(n["name"].lower().startswith("loopback") or n["name"].lower().startswith("lo") for n in ints)
    if not has_loopback:
        recs.append(("Add loopback0", "interface Loopback0\n ip address 10.0.0.1 255.255.255.255\n!"))

    # Basic hygiene/security recommendations
    recs.append(("Disable domain lookup & enable password encryption", "no ip domain-lookup\nservice password-encryption\n!"))
    recs.append(("Set enable secret and local admin user (change password)",
                "enable secret YourStrongSecret\nusername admin secret YourStrongSecret\n!"))
    recs.append(("SSH & VTY hardening",
                "ip domain-name example.local\ncrypto key generate rsa modulus 2048\nline vty 0 4\n transport input ssh\n login local\n exec-timeout 5 0\n!"))

    if bgp_asn and not (options.get("bgp_neighbors") or "").strip():
        recs.append(("BGP missing neighbors", f"! BGP ASN {bgp_asn} configured but no neighbors defined. Add 'neighbor x.x.x.x remote-as {bgp_asn}'"))

    return {"issues": issues, "recommendations": recs}

"""Minimal analyzer for Cisco config inputs.

This file contains a single, compact implementation to avoid duplication
and ensure the module imports correctly for the GUI and the unit tests.
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
    """Analyze provided options and return issues + recommendations.

    Supports keys: 'interfaces', 'bgp_asn', 'bgp_neighbors'.
    """
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

    # Recommend loopback if none present (unit test expects 'Add loopback0')
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
"""Analyzer for Cisco config inputs (clean).

This module intentionally contains a short, single implementation of the
analyzer to avoid accidental duplication and ensure import-time stability.
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
    """Analyze provided options and return simple issues + recommendations.

    The function is tolerant of missing keys in `options`.
    """
    issues: List[str] = []
    recs: List[Tuple[str, str]] = []

    interfaces_text = options.get("interfaces") or ""
    bgp_asn = (options.get("bgp_asn") or "").strip()

    ints = parse_interfaces(interfaces_text)

    # Validate IPs and detect duplicates
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
"""Analyzer for Cisco config inputs.

Provides a simple analyze_options(options) function used by the GUI and tests.

The module is intentionally minimal and focuses on:
 - parsing simple interface lines
 - detecting invalid IPs and duplicates
 - emitting a small set of useful security/configuration recommendations

The API:
    analyze_options(options: dict) -> { 'issues': [str], 'recommendations': [(title, snippet), ...] }
"""
from ipaddress import IPv4Address, IPv4Network
from typing import List, Dict, Any, Tuple


def parse_interfaces(text: str) -> List[Dict[str, str]]:
    """Parse interface lines like: "GigabitEthernet0/0 10.0.0.1/24".

    Returns list of dicts: { 'name': str, 'ip': str, 'raw': str }
    """
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
    """Analyze provided options and return issues + recommendations.

    options (partial): may include 'interfaces', 'bgp_asn', 'bgp_neighbors'.
    """
    issues: List[str] = []
    recommendations: List[Tuple[str, str]] = []

    interfaces_text = (options.get("interfaces") or "")
    bgp_asn = (options.get("bgp_asn") or "").strip()

    ints = parse_interfaces(interfaces_text)

    # Validate IPs and detect duplicates
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

    # Recommend Loopback if missing (test expects title containing 'loopback0')
    has_loopback = any(n["name"].lower().startswith("loopback") or n["name"].lower().startswith("lo") for n in ints)
    if not has_loopback:
        recommendations.append(("Add loopback0", "interface Loopback0\n ip address 10.0.0.1 255.255.255.255\n!"))

    # Basic security / hygiene recommendations
    recommendations.append(("Disable domain lookup & enable password encryption", "no ip domain-lookup\nservice password-encryption\n!"))
    recommendations.append(("Set enable secret and local admin user (change password)",
                            "enable secret YourStrongSecret\nusername admin secret YourStrongSecret\n!"))
    recommendations.append(("SSH & VTY hardening",
                            "ip domain-name example.local\ncrypto key generate rsa modulus 2048\nline vty 0 4\n transport input ssh\n login local\n exec-timeout 5 0\n!"))
    recommendations.append(("Logging and timestamps", "service timestamps log datetime msec\nlogging buffered 10000 debugging\n!"))
    recommendations.append(("Disable CDP on user-facing interfaces", "! consider: interface <if>\n no cdp enable\n!"))

    if bgp_asn and not (options.get("bgp_neighbors") or "").strip():
        recommendations.append(("BGP missing neighbors", f"! BGP ASN {bgp_asn} configured but no neighbors defined. Add 'neighbor x.x.x.x remote-as {bgp_asn}'"))

    return {"issues": issues, "recommendations": recommendations}
"""Small analyzer for Cisco config inputs.

Provides a single entrypoint `analyze_options(options)` which returns a dict:
  { 'issues': [str], 'recommendations': [(title, snippet), ...] }

This implementation is intentionally small and focused on router basics used
by the unit tests and the GUI.
"""
from ipaddress import IPv4Address, IPv4Network
from typing import List, Dict, Any


def parse_interfaces(text: str) -> List[Dict[str, str]]:
    """Parse simple interface lines of the form:
    <name> <ip> [optional comments]

    Returns a list of dicts with keys: name, ip, raw.
    """
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
    """Analyze provided options and return issues and recommendations.

    Expected input (partial): options may include 'interfaces', 'bgp_asn', and
    other fields. The function is tolerant of missing keys.
    """
    issues: List[str] = []
    recs: List[tuple] = []

    interfaces_text = (options.get("interfaces") or "")
    bgp_asn = (options.get("bgp_asn") or "").strip()

    ints = parse_interfaces(interfaces_text)

    # Validate IPs and detect duplicates
    seen_ips: Dict[str, str] = {}
    for it in ints:
        ipraw = it.get("ip", "")
        if not ipraw:
            issues.append(f"Missing IP on {it.get('name')}")
            continue
        if '/' in ipraw:
            try:
                net = IPv4Network(ipraw, strict=False)
            except Exception:
                issues.append(f"Invalid network/ip: '{ipraw}' on {it.get('name')}")
                continue
            ip_key = f"{net.network_address}/{net.prefixlen}"
        else:
            try:
                addr = IPv4Address(ipraw)
                ip_key = str(addr)
            except Exception:
                issues.append(f"Invalid IP: '{ipraw}' on {it.get('name')}")
                continue

        if ip_key in seen_ips:
            issues.append(f"Duplicate IP {ipraw} found on {it.get('name')} and {seen_ips[ip_key]}")
        else:
            seen_ips[ip_key] = it.get('name')

    # Recommend loopback if none provided
    has_loopback = any(
        i["name"].lower().startswith("loopback") or i["name"].lower().startswith("lo")
        """Analyzer for Cisco config inputs.

        Compact, single-file implementation to validate inputs and return recommendations.
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
            recommendations: List[Tuple[str, str]] = []

            interfaces_text = (options.get("interfaces") or "")
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

            has_loopback = any(n["name"].lower().startswith("loopback") or n["name"].lower().startswith("lo") for n in ints)
            if not has_loopback:
                recommendations.append(("Add loopback0", "interface Loopback0\n ip address 10.0.0.1 255.255.255.255\n!"))

            recommendations.append(("Disable domain lookup & enable password encryption", "no ip domain-lookup\nservice password-encryption\n!"))
            recommendations.append(("Set enable secret and local admin user (change password)",
                                    "enable secret YourStrongSecret\nusername admin secret YourStrongSecret\n!"))
            recommendations.append(("SSH & VTY hardening",
                                    "ip domain-name example.local\ncrypto key generate rsa modulus 2048\nline vty 0 4\n transport input ssh\n login local\n exec-timeout 5 0\n!"))
            recommendations.append(("Logging and timestamps", "service timestamps log datetime msec\nlogging buffered 10000 debugging\n!"))
            recommendations.append(("Disable CDP on user-facing interfaces", "! consider: interface <if>\n no cdp enable\n!"))

            if bgp_asn and not (options.get("bgp_neighbors") or "").strip():
                recommendations.append(("BGP missing neighbors", f"! BGP ASN {bgp_asn} configured but no neighbors defined. Add 'neighbor x.x.x.x remote-as {bgp_asn}'"))

            return {"issues": issues, "recommendations": recommendations}

    # Basic security snippets
    recs.append(("Disable domain lookup & enable password encryption", "no ip domain-lookup\nservice password-encryption\n!"))
    recs.append(("Set enable secret and local admin user (change password)",
                 "enable secret YourStrongSecret\nusername admin secret YourStrongSecret\n!"))
    recs.append(("SSH & VTY hardening",
                 "ip domain-name example.local\ncrypto key generate rsa modulus 2048\nline vty 0 4\n transport input ssh\n login local\n exec-timeout 5 0\n!"))
    recs.append(("Logging and timestamps", "service timestamps log datetime msec\nlogging buffered 10000 debugging\n!"))
    recs.append(("Disable CDP on user-facing interfaces", "! consider: interface <if>\n no cdp enable\n!"))

    if bgp_asn and not (options.get("bgp_neighbors") or "").strip():
        recs.append(("BGP missing neighbors", f"! BGP ASN {bgp_asn} configured but no neighbors defined. Add 'neighbor x.x.x.x remote-as {bgp_asn}'"))

    return {"issues": issues, "recommendations": recs}
"""Analyzer for Cisco config inputs (minimal and clean).

Provides a single entrypoint `analyze_options(options)` returning:
    { 'issues': [str], 'recommendations': [(title, snippet), ...] }

This file is intentionally small to avoid complex dependencies.
"""
from ipaddress import IPv4Address, IPv4Network
from typing import List, Dict, Any


def parse_interfaces(text: str) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
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
    recs: List[tuple] = []

    interfaces_text = options.get("interfaces") or ""
    ints = parse_interfaces(interfaces_text)
    bgp_asn = (options.get("bgp_asn") or "").strip()

    # Validate IPs and detect duplicates
    seen_ips: Dict[str, str] = {}
    for it in ints:
        ipraw = it["ip"]
        if '/' in ipraw:
            try:
                net = IPv4Network(ipraw, strict=False)
            except Exception:
                issues.append(f"Invalid network/ip: '{ipraw}' on {it['name']}")
                continue
            ip_key = f"{net.network_address}/{net.prefixlen}"
        else:
            try:
                addr = IPv4Address(ipraw)
                ip_key = str(addr)
            except Exception:
                issues.append(f"Invalid IP: '{ipraw}' on {it['name']}")
                continue

        if ip_key in seen_ips:
            issues.append(f"Duplicate IP {ipraw} found on {it['name']} and {seen_ips[ip_key]}")
        else:
            seen_ips[ip_key] = it['name']

    # Recommend Loopback if missing
    if not any(i['name'].lower().startswith('loopback') or i['name'].lower().startswith('lo') for i in ints):
        recs.append(("Add Loopback", "interface Loopback0\n ip address 10.0.0.1 255.255.255.255\n!"))

    # Basic security snippets
    recs.append(("Disable domain lookup & enable password encryption", "no ip domain-lookup\nservice password-encryption\n!"))
    recs.append(("Set enable secret and local admin user (change password)",
                 "enable secret YourStrongSecret\nusername admin secret YourStrongSecret\n!"))
    recs.append(("SSH & VTY hardening",
                 "ip domain-name example.local\ncrypto key generate rsa modulus 2048\nline vty 0 4\n transport input ssh\n login local\n exec-timeout 5 0\n!"))
    recs.append(("Logging and timestamps", "service timestamps log datetime msec\nlogging buffered 10000 debugging\n!"))
    recs.append(("Disable CDP on user-facing interfaces", "! consider: interface <if>\n no cdp enable\n!"))

    if bgp_asn and not (options.get("bgp_neighbors") or "").strip():
        recs.append(("BGP missing neighbors", f"! BGP ASN {bgp_asn} configured but no neighbors defined. Add 'neighbor x.x.x.x remote-as {bgp_asn}'"))

    return {"issues": issues, "recommendations": recs}
"""Analyzer for Cisco config inputs (minimal and clean).

Provides analyze_options(options) -> { 'issues': [...], 'recommendations': [...] }
"""
from ipaddress import IPv4Address, IPv4Network
from typing import List, Dict, Any


def parse_interfaces(text: str) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
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
    recs: List[tuple] = []

    interfaces_text = options.get("interfaces") or ""
    ints = parse_interfaces(interfaces_text)
    bgp_asn = (options.get("bgp_asn") or "").strip()

    seen_ips: Dict[str, str] = {}
    for it in ints:
        ipraw = it["ip"]
        if '/' in ipraw:
            try:
                net = IPv4Network(ipraw, strict=False)
            except Exception:
                issues.append(f"Invalid network/ip: '{ipraw}' on {it['name']}")
                continue
            ip_key = f"{net.network_address}/{net.prefixlen}"
        else:
            try:
                addr = IPv4Address(ipraw)
                ip_key = str(addr)
            except Exception:
                issues.append(f"Invalid IP: '{ipraw}' on {it['name']}")
                continue

        if ip_key in seen_ips:
            issues.append(f"Duplicate IP {ipraw} found on {it['name']} and {seen_ips[ip_key]}")
        else:
            seen_ips[ip_key] = it['name']

    # Recommend loopback if missing
    if not any(i['name'].lower().startswith('loopback') or i['name'].lower().startswith('lo') for i in ints):
        recs.append(("Add Loopback", "interface Loopback0\n ip address 10.0.0.1 255.255.255.255\n!"))

    # Basic security snippets
    recs.append(("Disable domain lookup & enable password encryption", "no ip domain-lookup\nservice password-encryption\n!"))
    recs.append(("Set enable secret and local admin user (change password)",
                 "enable secret YourStrongSecret\nusername admin secret YourStrongSecret\n!"))
    recs.append(("SSH & VTY hardening",
                 "ip domain-name example.local\ncrypto key generate rsa modulus 2048\nline vty 0 4\n transport input ssh\n login local\n exec-timeout 5 0\n!"))
    recs.append(("Logging and timestamps", "service timestamps log datetime msec\nlogging buffered 10000 debugging\n!"))
    recs.append(("Disable CDP on user-facing interfaces", "! consider: interface <if>\n no cdp enable\n!"))

    if bgp_asn and not (options.get("bgp_neighbors") or "").strip():
        recs.append(("BGP missing neighbors", f"! BGP ASN {bgp_asn} configured but no neighbors defined. Add 'neighbor x.x.x.x remote-as {bgp_asn}'"))

    return {"issues": issues, "recommendations": recs}
"""Analyzer for Cisco config inputs (minimal and clean).

Provides analyze_options(options) -> { 'issues': [...], 'recommendations': [...] }
"""
from ipaddress import IPv4Address, IPv4Network
from typing import List, Dict, Any


def parse_interfaces(text: str) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
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
    recs: List[tuple] = []

    interfaces_text = options.get("interfaces") or ""
    ints = parse_interfaces(interfaces_text)
    bgp_asn = (options.get("bgp_asn") or "").strip()

    # Validate IPs and detect duplicates
    seen_ips: Dict[str, str] = {}
    for it in ints:
        ipraw = it["ip"]
        if '/' in ipraw:
            try:
                net = IPv4Network(ipraw, strict=False)
            except Exception:
                issues.append(f"Invalid network/ip: '{ipraw}' on {it['name']}")
                continue
            ip_key = f"{net.network_address}/{net.prefixlen}"
        else:
            try:
                addr = IPv4Address(ipraw)
                ip_key = str(addr)
            except Exception:
                issues.append(f"Invalid IP: '{ipraw}' on {it['name']}")
                continue

        if ip_key in seen_ips:
            issues.append(f"Duplicate IP {ipraw} found on {it['name']} and {seen_ips[ip_key]}")
        else:
            seen_ips[ip_key] = it['name']

    # Recommend Loopback if missing
    if not any(i['name'].lower().startswith('loopback') or i['name'].lower().startswith('lo') for i in ints):
        recs.append(("Add Loopback", "interface Loopback0\n ip address 10.0.0.1 255.255.255.255\n!"))

    # Basic security snippets
    recs.append(("Disable domain lookup & enable password encryption", "no ip domain-lookup\nservice password-encryption\n!"))
    recs.append(("Set enable secret and local admin user (change password)",
                 "enable secret YourStrongSecret\nusername admin secret YourStrongSecret\n!"))
    recs.append(("SSH & VTY hardening",
                 "ip domain-name example.local\ncrypto key generate rsa modulus 2048\nline vty 0 4\n transport input ssh\n login local\n exec-timeout 5 0\n!"))
    recs.append(("Logging and timestamps", "service timestamps log datetime msec\nlogging buffered 10000 debugging\n!"))
    recs.append(("Disable CDP on user-facing interfaces", "! consider: interface <if>\n no cdp enable\n!"))

    if bgp_asn and not (options.get("bgp_neighbors") or "").strip():
        recs.append(("BGP missing neighbors", f"! BGP ASN {bgp_asn} configured but no neighbors defined. Add 'neighbor x.x.x.x remote-as {bgp_asn}'"))

    return {"issues": issues, "recommendations": recs}
"""Small analyzer for Cisco config inputs.

Provides a single entrypoint `analyze_options(options)` which returns a dict:
  { 'issues': [str], 'recommendations': [(title, snippet), ...] }

This implementation is intentionally small and focused on router basics.
"""
from ipaddress import IPv4Address, IPv4Network
from typing import List, Dict, Any


def parse_interfaces(text: str) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
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
    recs: List[tuple] = []

    interfaces_text = (options.get("interfaces") or "")
    bgp_asn = (options.get("bgp_asn") or "").strip()

    ints = parse_interfaces(interfaces_text)

    # Validate IPs and detect duplicates
    seen_ips: Dict[str, str] = {}
    for it in ints:
        ipraw = it["ip"]
        if '/' in ipraw:
            try:
                net = IPv4Network(ipraw, strict=False)
            except Exception:
                issues.append(f"Invalid network/ip: '{ipraw}' on {it['name']}")
                continue
            ip_key = f"{net.network_address}/{net.prefixlen}"
        else:
            try:
                addr = IPv4Address(ipraw)
                ip_key = str(addr)
            except Exception:
                issues.append(f"Invalid IP: '{ipraw}' on {it['name']}")
                continue

        if ip_key in seen_ips:
            issues.append(f"Duplicate IP {ipraw} found on {it['name']} and {seen_ips[ip_key]}")
        else:
            seen_ips[ip_key] = it['name']

    # Recommend loopback if none
    if not any(i['name'].lower().startswith('loopback') or i['name'].lower().startswith('lo') for i in ints):
        recs.append(("Add Loopback", "interface Loopback0\n ip address 10.0.0.1 255.255.255.255\n!"))

    # Security / hygiene recommendations
    recs.append(("Disable domain lookup & enable password encryption", "no ip domain-lookup\nservice password-encryption\n!"))
    recs.append(("Set enable secret and local admin user (change password)",
                 "enable secret YourStrongSecret\nusername admin secret YourStrongSecret\n!"))
    recs.append(("SSH & VTY hardening",
                 "ip domain-name example.local\ncrypto key generate rsa modulus 2048\nline vty 0 4\n transport input ssh\n login local\n exec-timeout 5 0\n!"))
    recs.append(("Logging and timestamps", "service timestamps log datetime msec\nlogging buffered 10000 debugging\n!"))
    recs.append(("Disable CDP on user-facing interfaces", "! consider: interface <if>\n no cdp enable\n!"))

    if bgp_asn and not (options.get("bgp_neighbors") or "").strip():
        recs.append(("BGP missing neighbors", f"! BGP ASN {bgp_asn} configured but no neighbors defined. Add 'neighbor x.x.x.x remote-as {bgp_asn}'"))

    return {"issues": issues, "recommendations": recs}
"""Analyze user inputs for coherence and produce security recommendations.

This module provides a small analyzer that checks interface definitions,
detects simple issues (invalid IPs, duplicates) and returns a list of
recommendations (config snippets) to improve security and completeness.
"""
from ipaddress import IPv4Address, IPv4Network
from typing import List, Dict, Any


def parse_interfaces(text: str) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
    """Analyze user inputs for coherence and produce security recommendations.

    This module provides a small analyzer that checks interface definitions,
    detects simple issues (invalid IPs, duplicates) and returns a list of
    recommendations (config snippets) to improve security and completeness.
    """
    from ipaddress import IPv4Address, IPv4Network
    from typing import List, Dict, Any


    def parse_interfaces(text: str) -> List[Dict[str, str]]:
        items: List[Dict[str, str]] = []
        for raw in text.splitlines():
            line = raw.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            name = parts[0]
            ip = parts[1]
            items.append({"name": name, "ip": ip, "raw": line})
        return items


    def analyze_options(options: Dict[str, Any]) -> Dict[str, Any]:
        issues: List[str] = []
        recs: List[tuple] = []

        interfaces_text = options.get("interfaces", "") or ""
        bgp_asn = (options.get("bgp_asn") or "").strip()

        ints = parse_interfaces(interfaces_text)

        # Check for invalid IPs or duplicate IPs
        seen_ips: Dict[str, str] = {}
        for it in ints:
            ipraw = it["ip"]
            if '/' in ipraw:
                try:
                    net = IPv4Network(ipraw, strict=False)
                except Exception:
                    issues.append(f"Invalid network/ip: '{ipraw}' on {it['name']}")
                    continue
                ip_key = str(net.network_address) + '/' + str(net.prefixlen)
            else:
                try:
                    addr = IPv4Address(ipraw)
                    ip_key = str(addr)
                except Exception:
                    issues.append(f"Invalid IP: '{ipraw}' on {it['name']}")
                    continue

            if ip_key in seen_ips:
                issues.append(f"Duplicate IP {ipraw} found on {it['name']} and {seen_ips[ip_key]}")
            else:
                seen_ips[ip_key] = it['name']

        # Recommend loopback if none
        loopback_present = any(i['name'].lower().startswith('loopback') or i['name'].lower().startswith('lo') for i in ints)
        if not loopback_present:
            recs.append(("Add loopback0", "interface Loopback0\n ip address 10.0.0.1 255.255.255.255\n!"))

        # Basic security recommendations
        recs.append(("Disable domain lookup & enable password encryption", "no ip domain-lookup\nservice password-encryption\n!"))
        recs.append(("Set enable secret and username with secret (change 'YourStrongSecret')",
                     "enable secret YourStrongSecret\nusername admin secret YourStrongSecret\n!"))
        recs.append(("SSH and VTY hardening",
                     "ip domain-name example.local\ncrypto key generate rsa modulus 2048\nline vty 0 4\n transport input ssh\n login local\n exec-timeout 5 0\n!"))
        recs.append(("Logging and timestamps", "service timestamps log datetime msec\nlogging buffered 10000 debugging\n!"))
        recs.append(("Disable CDP on all user interfaces", "! consider: interface <if>\n  no cdp enable\n!"))

        # BGP recommendations
        if bgp_asn and not (options.get("bgp_neighbors") or "").strip():
            recs.append(("BGP missing neighbors", f"! You set BGP ASN {bgp_asn} but no neighbors configured. Add 'neighbor x.x.x.x remote-as {bgp_asn}' lines."))

        return {"issues": issues, "recommendations": recs}
                seen_ips[ip_key] = it['name']

        # Recommend loopback if none
        loopback_present = any(i['name'].lower().startswith('loopback') or i['name'].lower().startswith('lo') for i in ints)
        if not loopback_present:
            recs.append(("Add loopback0", "interface Loopback0\n ip address 10.0.0.1 255.255.255.255\n!"))

        # Basic security recommendations
        recs.append(("Disable domain lookup & enable password encryption", "no ip domain-lookup\nservice password-encryption\n!"))
        recs.append(("Set enable secret and username with secret (change 'YourStrongSecret')",
                     "enable secret YourStrongSecret\nusername admin secret YourStrongSecret\n!"))
        recs.append(("SSH and VTY hardening",
                     "ip domain-name example.local\ncrypto key generate rsa modulus 2048\nline vty 0 4\n transport input ssh\n login local\n exec-timeout 5 0\n!"))
        recs.append(("Logging and timestamps", "service timestamps log datetime msec\nlogging buffered 10000 debugging\n!"))
        recs.append(("Disable CDP on all user interfaces", "! consider: interface <if>\n  no cdp enable\n!"))

        # BGP recommendations
        if bgp_asn and not (options.get("bgp_neighbors") or "").strip():
            recs.append(("BGP missing neighbors", f"! You set BGP ASN {bgp_asn} but no neighbors configured. Add 'neighbor x.x.x.x remote-as {bgp_asn}' lines."))

        return {"issues": issues, "recommendations": recs}
    recs: List[tuple] = []

    hostname = options.get("hostname") or ""
    interfaces_text = options.get("interfaces", "")
    bgp_asn = (options.get("bgp_asn") or "").strip()

    ints = parse_interfaces(interfaces_text)

    # Check for invalid IPs or duplicate IPs
    seen_ips: Dict[str, str] = {}
    for it in ints:
        ipraw = it["ip"]
        if '/' in ipraw:
            try:
                net = IPv4Network(ipraw, strict=False)
            except Exception:
                issues.append(f"Invalid network/ip: '{ipraw}' on {it['name']}")
                continue
            ip_key = str(net.network_address) + '/' + str(net.prefixlen)
        else:
            try:
                addr = IPv4Address(ipraw)
                ip_key = str(addr)
            except Exception:
                issues.append(f"Invalid IP: '{ipraw}' on {it['name']}")
                continue

        if ip_key in seen_ips:
            issues.append(f"Duplicate IP {ipraw} found on {it['name']} and {seen_ips[ip_key]}")
        else:
            seen_ips[ip_key] = it['name']

    # Recommend loopback if none
    loopback_present = any(i['name'].lower().startswith('loopback') or i['name'].lower().startswith('lo') for i in ints)
    if not loopback_present:
        recs.append(("Add loopback0", "interface Loopback0\n ip address 10.0.0.1 255.255.255.255\n!"))

    # Basic security recommendations
    recs.append(("Disable domain lookup & enable password encryption", "no ip domain-lookup\nservice password-encryption\n!"))
    recs.append(("Set enable secret and username with secret (change 'YourStrongSecret')",
                 "enable secret YourStrongSecret\nusername admin secret YourStrongSecret\n!"))
    recs.append(("SSH and VTY hardening",
                 "ip domain-name example.local\ncrypto key generate rsa modulus 2048\nline vty 0 4\n transport input ssh\n login local\n exec-timeout 5 0\n!"))
    recs.append(("Logging and timestamps", "service timestamps log datetime msec\nlogging buffered 10000 debugging\n!"))
    recs.append(("Disable CDP on all user interfaces", "! consider: interface <if>\n  no cdp enable\n!"))

    # BGP recommendations
    if bgp_asn and not options.get("bgp_neighbors", "").strip():
        recs.append(("BGP missing neighbors", f"! You set BGP ASN {bgp_asn} but no neighbors configured. Add 'neighbor x.x.x.x remote-as {bgp_asn}' lines."))

    return {"issues": issues, "recommendations": recs}
"""Analyze user inputs for coherence and produce security recommendations.

Functions:
 - analyze_options(options) -> dict with 'issues' and 'recommendations'

Recommendations are tuples (title, snippet) where snippet is a config block.
"""
from ipaddress import IPv4Address, IPv4Network
from typing import List, Dict


def parse_interfaces(text: str) -> List[Dict]:
    items = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        name = parts[0]
        ip = parts[1]
        items.append({"name": name, "ip": ip, "raw": line})
    return items


def ip_str_to_ipv4(ipstr: str):
    try:
        if '/' in ipstr:
            return IPv4Network(ipstr, strict=False)
        """Analyzer for Cisco config inputs (minimal and clean).

        Provides analyze_options(options) -> { 'issues': [...], 'recommendations': [...] }
        """
        from ipaddress import IPv4Address, IPv4Network
        from typing import List, Dict, Any


        def parse_interfaces(text: str) -> List[Dict[str, str]]:
            items: List[Dict[str, str]] = []
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
            recs: List[tuple] = []

            interfaces_text = options.get("interfaces") or ""
            ints = parse_interfaces(interfaces_text)
            bgp_asn = (options.get("bgp_asn") or "").strip()

            # Validate IPs and detect duplicates
            seen_ips: Dict[str, str] = {}
            for it in ints:
                ipraw = it["ip"]
                if '/' in ipraw:
                    try:
                        net = IPv4Network(ipraw, strict=False)
                    except Exception:
                        issues.append(f"Invalid network/ip: '{ipraw}' on {it['name']}")
                        continue
                    ip_key = f"{net.network_address}/{net.prefixlen}"
                else:
                    try:
                        addr = IPv4Address(ipraw)
                        ip_key = str(addr)
                    except Exception:
                        issues.append(f"Invalid IP: '{ipraw}' on {it['name']}")
                        continue

                if ip_key in seen_ips:
                    issues.append(f"Duplicate IP {ipraw} found on {it['name']} and {seen_ips[ip_key]}")
                else:
                    seen_ips[ip_key] = it['name']

            # Recommend Loopback if missing
            if not any(i['name'].lower().startswith('loopback') or i['name'].lower().startswith('lo') for i in ints):
                recs.append(("Add Loopback", "interface Loopback0\n ip address 10.0.0.1 255.255.255.255\n!"))

            # Basic security snippets
            recs.append(("Disable domain lookup & enable password encryption", "no ip domain-lookup\nservice password-encryption\n!"))
            recs.append(("Set enable secret and local admin user (change password)",
                         "enable secret YourStrongSecret\nusername admin secret YourStrongSecret\n!"))
            recs.append(("SSH & VTY hardening",
                         "ip domain-name example.local\ncrypto key generate rsa modulus 2048\nline vty 0 4\n transport input ssh\n login local\n exec-timeout 5 0\n!"))
            recs.append(("Logging and timestamps", "service timestamps log datetime msec\nlogging buffered 10000 debugging\n!"))
            recs.append(("Disable CDP on user-facing interfaces", "! consider: interface <if>\n no cdp enable\n!"))

            if bgp_asn and not (options.get("bgp_neighbors") or "").strip():
                recs.append(("BGP missing neighbors", f"! BGP ASN {bgp_asn} configured but no neighbors defined. Add 'neighbor x.x.x.x remote-as {bgp_asn}'"))

            return {"issues": issues, "recommendations": recs}

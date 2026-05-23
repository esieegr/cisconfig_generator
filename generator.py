"""Cisco-like configuration generator utilities.

Simple, dependency-free helpers to assemble IOS-like configuration snippets
for hostname, interfaces, MPLS, OSPF and BGP. Designed to be easy to read
and extend.
"""
from ipaddress import IPv4Network


def cidr_to_netmask(cidr: str) -> str:
    """Convert CIDR like 10.0.0.0/24 to netmask '255.255.255.0'."""
    # accept either 'ip/prefix' or an ip network 'ip' (assume /24)
    if '/' not in cidr:
        cidr = cidr.rstrip() + '/24'
    return str(IPv4Network(cidr, strict=False).netmask)


def generate_hostname(name: str) -> str:
    if not name:
        name = "Router"
    return f"hostname {name}\n!\n"


def generate_interfaces(text: str) -> str:
    """Parse a small user textarea describing interfaces.

    Expected input per non-empty line:
      <if-name> <ip/cidr> [description text]

    Example:
      GigabitEthernet0/0 10.0.0.1/24 WAN link
    """
    out = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        if_name = parts[0]
        ip_cidr = parts[1]
        desc = " ".join(parts[2:]) if len(parts) > 2 else None
        # If user provided IP without /prefix, assume /24 by default
        if '/' not in ip_cidr:
            ip_addr = ip_cidr
            guessed = ip_cidr + '/24'
        else:
            ip_addr = ip_cidr.split('/')[0]
            guessed = ip_cidr
        try:
            mask = cidr_to_netmask(guessed)
            ip = ip_addr
        except Exception:
            ip = ip_addr
            mask = "255.255.255.255"

        out.append(f"interface {if_name}")
        out.append(f" ip address {ip} {mask}")
        if desc:
            out.append(f" description {desc}")
        out.append(" no shutdown")
        out.append("!")

    return "\n".join(out) + ("\n" if out else "")


def generate_mpls(enabled: bool) -> str:
    if not enabled:
        return ""
    return "mpls ip\n!\n"


def generate_ospf(process_id: str, networks_text: str) -> str:
    if not process_id and not networks_text.strip():
        return ""
    pid = process_id.strip() or "1"
    out = [f"router ospf {pid}"]
    for raw in networks_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        # Accept formats like:
        #  - 10.0.0.0/24 area 0
        #  - 10.0.0.0 area 0
        #  - 10.0.0.0/24
        parts = line.split()
        net_part = parts[0]
        rest = " ".join(parts[1:]) if len(parts) > 1 else ""

        # If net_part has no prefix, assume /24 for wildcard computation
        if '/' not in net_part:
            cidr = net_part + '/24'
            network_ip = net_part
        else:
            cidr = net_part
            network_ip = net_part.split('/')[0]

        wildcard = ipv4_cidr_to_wildcard(cidr)
        area_clause = ''
        if 'area' in rest:
            area_clause = rest
        else:
            # default area 0 if nothing provided
            area_clause = rest or 'area 0'

        out.append(f" network {network_ip} {wildcard} {area_clause}")

    out.append("!")
    return "\n".join(out) + "\n"


def ipv4_cidr_to_wildcard(cidr: str) -> str:
    try:
        # ensure we have a prefix
        if '/' not in cidr:
            cidr = cidr.rstrip() + '/24'
        net = IPv4Network(cidr, strict=False)
        mask = str(net.netmask)
        wildcard_octets = [str(255 - int(o)) for o in mask.split('.')]
        return ".".join(wildcard_octets)
    except Exception:
        return "0.0.0.0"


def generate_bgp(asn: str, neighbors_text: str) -> str:
    if not asn:
        return ""
    out = [f"router bgp {asn}"]
    for raw in neighbors_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        # Accept: <neighbor-ip> [remote-as <asn>]
        out.append(f" neighbor {line}")
    out.append("!")
    return "\n".join(out) + "\n"


def generate_full_config(options: dict) -> str:
    """Assemble a full configuration from options dictionary.

    Expected options keys: hostname, interfaces (text), mpls (bool), ospf_pid,
    ospf_networks (text), bgp_asn, bgp_neighbors (text)
    """
    parts = []
    parts.append(generate_hostname(options.get("hostname", "")))
    parts.append(generate_interfaces(options.get("interfaces", "")))
    parts.append(generate_mpls(bool(options.get("mpls", False))))
    parts.append(generate_ospf(str(options.get("ospf_pid", "")).strip(), options.get("ospf_networks", "")))
    parts.append(generate_bgp(str(options.get("bgp_asn", "")).strip(), options.get("bgp_neighbors", "")))

    # Trim and join
    return "\n".join([p.strip() for p in parts if p and p.strip()]) + "\n"

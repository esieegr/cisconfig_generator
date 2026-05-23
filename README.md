Cisco Config Generator
======================

Small Python/Tkinter application to generate Cisco-like configurations (hostname,
interfaces, MPLS, OSPF, BGP) and export them to a file.

Requirements
------------

- Python 3.8+ (Tkinter included on Windows installers)

Running
-------

Open PowerShell and run:

```powershell
python .\app.py
```

Usage
-----

- Fill hostname, interfaces (one per line: name ip/cidr description), check MPLS if needed.
- Provide OSPF process id and networks (CIDR or 'ip wildcard area').
- Provide BGP ASN and neighbors (one per line, e.g. '1.2.3.4 remote-as 65001').
- Click Generate to view the configuration. Click Export to save as a .cfg or .txt file.

Tests
-----

Run the unit tests with:

```powershell
python -m unittest discover -v
```

Notes
-----

This is a minimal starter app designed to be extended. The generator produces
human-readable IOS-like configuration snippets and is not a replacement for
official device configuration tools. Contributions welcome.


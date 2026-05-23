import unittest
from generator import (
    cidr_to_netmask,
    generate_hostname,
    generate_interfaces,
    generate_mpls,
    generate_ospf,
    generate_bgp,
    generate_full_config,
)


class TestGenerator(unittest.TestCase):
    def test_cidr_to_netmask(self):
        self.assertEqual(cidr_to_netmask("10.0.0.0/24"), "255.255.255.0")

    def test_hostname(self):
        self.assertIn("hostname R1", generate_hostname("R1"))

    def test_interfaces(self):
        txt = "GigabitEthernet0/0 10.0.0.1/24 link to isp"
        out = generate_interfaces(txt)
        self.assertIn("interface GigabitEthernet0/0", out)
        self.assertIn("ip address 10.0.0.1 255.255.255.0", out)

    def test_mpls(self):
        self.assertIn("mpls ip", generate_mpls(True))

    def test_ospf(self):
        out = generate_ospf("1", "10.0.0.0/24 area 0")
        self.assertIn("router ospf 1", out)

    def test_bgp(self):
        out = generate_bgp("65000", "1.2.3.4 remote-as 65001")
        self.assertIn("router bgp 65000", out)

    def test_full(self):
        opts = {
            "hostname": "R1",
            "interfaces": "GigabitEthernet0/0 10.0.0.1/24",
            "mpls": True,
            "ospf_pid": "1",
            "ospf_networks": "10.0.0.0/24 area 0",
            "bgp_asn": "65000",
            "bgp_neighbors": "1.2.3.4 remote-as 65001",
        }
        cfg = generate_full_config(opts)
        self.assertIn("hostname R1", cfg)
        self.assertIn("mpls ip", cfg)


if __name__ == "__main__":
    unittest.main()

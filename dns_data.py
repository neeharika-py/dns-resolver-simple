"""
dns_data.py
-----------
All the mock DNS data lives here:
  1. which name servers exist (root, TLD, authoritative)
  2. which records each zone holds

Each record is written as:  (name, type, value, ttl_in_seconds)

To add your own website, see the "How to add a domain" section in README.md.
"""

# Fake network delay for each kind of server (milliseconds).
# Used to show how much time the cache saves.
LATENCY_MS = {
    "Root": 40,
    "TLD": 25,
    "Authoritative": 10,
}

# How long to remember "this name does not exist" answers (seconds)
NEGATIVE_TTL = 60

# ---------------------------------------------------------------------------
# NAME SERVERS
#   (server name,            mock IP,          level,           zones it manages)
# ---------------------------------------------------------------------------
SERVERS = [
    ("a.root-servers.net",     "198.41.0.4",     "Root",          ["."]),

    ("a.gtld-servers.net",     "192.5.6.30",     "TLD",           ["com", "net"]),
    ("a0.org-servers.net",     "199.19.56.1",    "TLD",           ["org"]),
    ("ns1.registry.in",        "37.209.192.12",  "TLD",           ["in"]),
    ("a.in-addr-servers.arpa", "199.180.182.53", "TLD",           ["in-addr.arpa"]),

    ("ns1.example.com",        "203.0.113.53",   "Authoritative", ["example.com", "113.0.203.in-addr.arpa"]),
    ("ns1.shopkart.com",       "198.51.100.53",  "Authoritative", ["shopkart.com"]),
    ("dns.cloudhost.net",      "192.0.2.53",     "Authoritative", ["cloudhost.net", "openwiki.org"]),
    ("ns.university.ac.in",    "198.51.100.200", "Authoritative", ["university.ac.in"]),
]

# ---------------------------------------------------------------------------
# ZONES
# An NS record for a name *below* the zone means "I don't handle this,
# ask that server instead" (a delegation). The A record next to it tells
# the resolver that server's IP address (called a "glue" record).
# ---------------------------------------------------------------------------
ZONES = {
    # ----- Root zone: knows only who runs each top-level domain -----
    ".": [
        ("com",          "NS", "a.gtld-servers.net",     172800),
        ("net",          "NS", "a.gtld-servers.net",     172800),
        ("org",          "NS", "a0.org-servers.net",     172800),
        ("in",           "NS", "ns1.registry.in",        172800),
        ("in-addr.arpa", "NS", "a.in-addr-servers.arpa", 172800),
        # glue
        ("a.gtld-servers.net",     "A", "192.5.6.30",     172800),
        ("a0.org-servers.net",     "A", "199.19.56.1",    172800),
        ("ns1.registry.in",        "A", "37.209.192.12",  172800),
        ("a.in-addr-servers.arpa", "A", "199.180.182.53", 172800),
    ],

    # ----- TLD zones: know who runs each domain under them -----
    "com": [
        ("example.com",      "NS", "ns1.example.com",  172800),
        ("ns1.example.com",  "A",  "203.0.113.53",     172800),
        ("shopkart.com",     "NS", "ns1.shopkart.com", 172800),
        ("ns1.shopkart.com", "A",  "198.51.100.53",    172800),
    ],
    "net": [
        ("cloudhost.net",      "NS", "dns.cloudhost.net", 172800),
        ("dns.cloudhost.net",  "A",  "192.0.2.53",        172800),
    ],
    "org": [
        ("openwiki.org",       "NS", "dns.cloudhost.net", 86400),
        ("dns.cloudhost.net",  "A",  "192.0.2.53",        86400),
    ],
    "in": [
        ("university.ac.in",     "NS", "ns.university.ac.in", 86400),
        ("ns.university.ac.in",  "A",  "198.51.100.200",      86400),
    ],
    "in-addr.arpa": [
        ("113.0.203.in-addr.arpa", "NS", "ns1.example.com", 86400),
        ("ns1.example.com",        "A",  "203.0.113.53",    86400),
    ],

    # ----- Authoritative zones: hold the real answers -----
    "example.com": [
        ("example.com",      "SOA",   "ns1.example.com admin.example.com 2026100101 3600 600 86400 300", 3600),
        ("example.com",      "NS",    "ns1.example.com",      3600),
        ("example.com",      "A",     "203.0.113.10",         300),
        ("example.com",      "AAAA",  "2001:db8::10",         300),
        ("example.com",      "MX",    "10 mail.example.com",  3600),
        ("example.com",      "MX",    "20 backup.example.com", 3600),
        ("example.com",      "TXT",   "v=spf1 mx -all",       3600),
        ("www.example.com",  "CNAME", "example.com",          300),
        ("mail.example.com", "A",     "203.0.113.25",         3600),
        ("backup.example.com", "A",   "203.0.113.26",         3600),
        ("ftp.example.com",  "A",     "203.0.113.21",         600),
        ("docs.example.com", "CNAME", "openwiki.org",         600),
        ("ns1.example.com",  "A",     "203.0.113.53",         3600),
    ],
    "113.0.203.in-addr.arpa": [
        ("10.113.0.203.in-addr.arpa", "PTR", "example.com",      3600),
        ("21.113.0.203.in-addr.arpa", "PTR", "ftp.example.com",  3600),
        ("25.113.0.203.in-addr.arpa", "PTR", "mail.example.com", 3600),
    ],
    "shopkart.com": [
        ("shopkart.com",      "A",     "198.51.100.10",               300),
        ("shopkart.com",      "MX",    "10 mail.shopkart.com",        3600),
        ("shopkart.com",      "TXT",   "site-verification=sk-7f3a9c", 3600),
        ("mail.shopkart.com", "A",     "198.51.100.25",               3600),
        ("www.shopkart.com",  "CNAME", "cdn.shopkart.com",            300),
        ("cdn.shopkart.com",  "CNAME", "shopkart.edge.cloudhost.net", 300),
    ],
    "cloudhost.net": [
        ("shopkart.edge.cloudhost.net", "A",    "192.0.2.101",        60),
        ("shopkart.edge.cloudhost.net", "A",    "192.0.2.102",        60),
        ("shopkart.edge.cloudhost.net", "AAAA", "2001:db8:cafe::101", 60),
    ],
    "openwiki.org": [
        ("openwiki.org",     "A",     "192.0.2.80",                  600),
        ("openwiki.org",     "TXT",   "Free knowledge for everyone", 3600),
        ("www.openwiki.org", "CNAME", "openwiki.org",                600),
    ],
    "university.ac.in": [
        ("university.ac.in",        "A",     "198.51.100.201",          600),
        ("university.ac.in",        "MX",    "5 mail.university.ac.in", 3600),
        ("mail.university.ac.in",   "A",     "198.51.100.203",          3600),
        ("www.university.ac.in",    "CNAME", "university.ac.in",        600),
        ("portal.university.ac.in", "A",     "198.51.100.202",          600),
    ],
}

# Short explanations shown in the menu
RECORD_TYPES = {
    "A":     "IPv4 address of a name             e.g. example.com -> 203.0.113.10",
    "AAAA":  "IPv6 address of a name             e.g. example.com -> 2001:db8::10",
    "CNAME": "Alias (another name for a name)    e.g. www.example.com -> example.com",
    "MX":    "Mail server for a domain           e.g. 10 mail.example.com",
    "NS":    "Name server in charge of a zone    e.g. ns1.example.com",
    "TXT":   "Free text (SPF, verification)      e.g. v=spf1 mx -all",
    "SOA":   "Zone settings (Start of Authority) e.g. admin email, serial number",
    "PTR":   "Reverse lookup: IP -> name         e.g. 203.0.113.10 -> example.com",
}

"""
dns_server.py
-------------
A mock name server. It answers one question: "What is <name> <type>?"

The reply is one of:
  ANSWER    - "Here are the records."               (I am in charge of this name)
  REFERRAL  - "Not me. Ask this other server."      (the name belongs to a child zone)
  NXDOMAIN  - "This name does not exist."
  NODATA    - "The name exists, but not that type."
  REFUSED   - "I don't handle that part of DNS at all."
"""


def is_inside(name, zone):
    """True if `name` belongs under `zone`. Example: www.example.com is inside example.com"""
    return zone == "." or name == zone or name.endswith("." + zone)


def make_record(row):
    """Turn a tuple from dns_data into a small dictionary."""
    name, rtype, value, ttl = row
    return {"name": name, "type": rtype, "value": value, "ttl": ttl}


class NameServer:
    def __init__(self, name, ip, level, zone_names, all_zones):
        self.name = name
        self.ip = ip
        self.level = level                    # "Root", "TLD" or "Authoritative"
        self.zones = {}                       # zone name -> list of records
        for zone in zone_names:
            self.zones[zone] = [make_record(row) for row in all_zones[zone]]
        self.queries_received = 0

    # ------------------------------------------------------------------
    def handle_query(self, qname, qtype):
        self.queries_received += 1

        zone = self.find_zone(qname)
        if zone is None:
            return self.reply("REFUSED", zone)
        records = self.zones[zone]

        # Step 1: does this name belong to a child zone? -> send a referral
        child_zone, ns_names = self.find_delegation(qname, zone, records)
        if child_zone:
            next_servers = []
            for ns in ns_names:
                next_servers.append((ns, self.find_glue_ip(ns, records)))
            return self.reply("REFERRAL", zone, next_zone=child_zone, next_servers=next_servers)

        # Step 2: we are in charge -> look for the records
        answers = []
        name = qname
        for _ in range(5):                        # follow at most 5 aliases
            matches = [r for r in records if r["name"] == name and r["type"] == qtype]
            if matches:
                answers += matches
                break
            alias = [r for r in records if r["name"] == name and r["type"] == "CNAME"]
            if alias and qtype != "CNAME":
                answers += alias
                name = alias[0]["value"]
                if is_inside(name, zone):
                    continue                      # alias points inside our zone: keep going
            break

        if answers:
            return self.reply("ANSWER", zone, answers=answers)

        name_exists = any(r["name"] == qname for r in records) or qname == zone
        if name_exists:
            return self.reply("NODATA", zone)
        return self.reply("NXDOMAIN", zone)

    # ------------------------------------------------------------------
    def find_zone(self, qname):
        """Pick the most specific zone we manage that contains the name."""
        best = None
        for zone in self.zones:
            if is_inside(qname, zone):
                if best is None or len(zone) > len(best):
                    best = zone
        return best

    @staticmethod
    def find_delegation(qname, zone, records):
        """Find an NS record below our zone that covers qname."""
        best_child = None
        for r in records:
            if r["type"] == "NS" and r["name"] != zone and is_inside(qname, r["name"]):
                if best_child is None or len(r["name"]) > len(best_child):
                    best_child = r["name"]
        if best_child is None:
            return None, []
        ns_names = [r["value"] for r in records if r["type"] == "NS" and r["name"] == best_child]
        return best_child, ns_names

    @staticmethod
    def find_glue_ip(ns_name, records):
        for r in records:
            if r["name"] == ns_name and r["type"] == "A":
                return r["value"]
        return None

    def reply(self, status, zone, answers=None, next_zone=None, next_servers=None):
        return {
            "status": status,
            "zone": zone,
            "answers": answers or [],
            "next_zone": next_zone,
            "next_servers": next_servers or [],
        }

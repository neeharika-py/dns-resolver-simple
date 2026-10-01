"""
resolver.py
-----------
The resolver walks down the DNS tree to find an answer:

    Root server  ->  TLD server (.com)  ->  Authoritative server (example.com)

Two query types are supported:

  RECURSIVE  - The client asks a local resolver ONE question ("find it for me").
               The resolver does all the walking and remembers answers in its CACHE.

  ITERATIVE  - The client walks the tree itself: it asks the root, gets told
               "ask .com", asks .com, gets told "ask example.com", and so on.
               No resolver, so no cache.
"""

import time

from dns_data import LATENCY_MS, NEGATIVE_TTL, SERVERS, ZONES
from dns_server import NameServer

MAX_ALIASES = 5      # stop after following this many CNAMEs
MAX_STEPS = 10       # stop after this many referrals (protects against loops)


def clean_name(name):
    """'WWW.Example.com.' -> 'www.example.com'"""
    name = name.strip().lower()
    if name != "." and name.endswith("."):
        name = name[:-1]
    return name


class Resolver:
    def __init__(self):
        self.servers = [NameServer(name, ip, level, zones, ZONES)
                        for name, ip, level, zones in SERVERS]
        self.servers_by_ip = {s.ip: s for s in self.servers}
        self.root_server = self.servers[0]
        self.cache = {}       # (name, type) -> {"status", "answers", "expires"}

    # ==================================================================
    def resolve(self, name, qtype, mode="recursive"):
        """
        Returns a dictionary:
          status   - FOUND / NXDOMAIN / NODATA / FAILED
          answers  - list of records
          steps    - everything that happened, in order (for printing)
          delays   - list of delays in ms (one per server contacted)
        """
        name = clean_name(name)
        qtype = qtype.strip().upper()
        use_cache = (mode == "recursive")
        steps = []
        all_answers = []

        status = "FAILED"
        for _ in range(MAX_ALIASES):
            status, answers = self.lookup(name, qtype, steps, use_cache)
            all_answers += answers
            if status != "FOUND":
                break

            # Follow the CNAME chain inside the answer to see where it ends
            end_name = name
            for record in answers:
                if record["name"] == end_name and record["type"] == "CNAME":
                    end_name = record["value"]

            got_it = any(r["name"] == end_name and r["type"] == qtype for r in answers)
            if got_it or end_name == name:
                break

            # The alias points to a name in another zone -> start a new lookup
            steps.append({"kind": "note",
                          "text": f"{name} is an alias for {end_name}. Starting a new lookup for {end_name}."})
            name = end_name

        delays = [s["delay"] for s in steps if s["kind"] == "query"]
        return {"status": status, "answers": all_answers, "steps": steps, "delays": delays}

    # ==================================================================
    def lookup(self, name, qtype, steps, use_cache):
        """Find one name: check the cache, otherwise start at the root and follow referrals."""
        if use_cache:
            cached = self.cache_get(name, qtype)
            if cached:
                steps.append({"kind": "cache", "name": name, "qtype": qtype,
                              "status": cached["status"], "answers": cached["answers"]})
                return cached["status"], cached["answers"]

        server = self.root_server
        for _ in range(MAX_STEPS):
            reply = server.handle_query(name, qtype)
            steps.append({"kind": "query", "server": server, "name": name, "qtype": qtype,
                          "reply": reply, "delay": LATENCY_MS[server.level]})

            if reply["status"] == "REFERRAL":
                next_name, next_ip = reply["next_servers"][0]
                server = self.servers_by_ip.get(next_ip)
                if server is None:
                    return "FAILED", []
                continue

            if reply["status"] == "ANSWER":
                status = "FOUND"
            elif reply["status"] in ("NXDOMAIN", "NODATA"):
                status = reply["status"]
            else:
                status = "FAILED"

            if use_cache and status != "FAILED":
                self.cache_put(name, qtype, status, reply["answers"])
            return status, reply["answers"]

        return "FAILED", []

    # ==================================================================
    # Cache
    def cache_put(self, name, qtype, status, answers):
        if answers:
            ttl = min(r["ttl"] for r in answers)   # the group lives as long as its shortest TTL
        else:
            ttl = NEGATIVE_TTL                    # "does not exist" answers are kept briefly
        self.cache[(name, qtype)] = {
            "status": status,
            "answers": answers,
            "expires": time.time() + ttl,
        }

    def cache_get(self, name, qtype):
        entry = self.cache.get((name, qtype))
        if entry is None:
            return None
        seconds_left = int(entry["expires"] - time.time())
        if seconds_left <= 0:
            del self.cache[(name, qtype)]         # expired
            return None
        # Show the TTL counting down, like a real resolver does
        answers = [dict(r, ttl=min(r["ttl"], seconds_left)) for r in entry["answers"]]
        return {"status": entry["status"], "answers": answers}

    def cache_entries(self):
        rows = []
        for (name, qtype) in list(self.cache):
            entry = self.cache_get(name, qtype)
            if entry:
                left = int(self.cache[(name, qtype)]["expires"] - time.time())
                rows.append((name, qtype, entry["status"], entry["answers"], left))
        return rows

    def clear_cache(self):
        self.cache.clear()

"""
main.py
-------
DNS Resolver Simulation - run this file:

    python main.py

Everything is shown in the terminal through a simple menu.
"""

import ipaddress

from dns_data import RECORD_TYPES, ZONES
from resolver import Resolver, clean_name

LINE = "=" * 64
THIN = "-" * 64



def describe_reply(reply, qtype):
    """One-line, plain-English version of a server's reply."""
    status = reply["status"]
    if status == "REFERRAL":
        ns_name, ns_ip = reply["next_servers"][0]
        return f"REFERRAL  -> \"Not me. Ask the '{reply['next_zone']}' server: {ns_name} ({ns_ip})\""
    if status == "ANSWER":
        values = ", ".join(f"{r['type']} {r['value']}" for r in reply["answers"])
        return f"ANSWER    -> {values}"
    if status == "NXDOMAIN":
        return "NXDOMAIN  -> \"This name does not exist.\""
    if status == "NODATA":
        return f"NO DATA   -> \"The name exists, but has no {qtype} record.\""
    return f"{status}"


def print_answers(answers):
    print(f"   {'NAME':<30}{'TYPE':<7}{'VALUE':<30}TTL")
    for r in answers:
        print(f"   {r['name']:<30}{r['type']:<7}{r['value']:<30}{r['ttl']}s")


def print_result(name, qtype, mode, result):
    asker = "Resolver" if mode == "recursive" else "Client"

    print()
    print(LINE)
    print(f" QUERY : {clean_name(name)}   TYPE : {qtype}   MODE : {mode.upper()}")
    print(LINE)
    if mode == "recursive":
        print(" Client -> Local Resolver : \"Please find this for me.\"  (recursive query, RD=1)")
    else:
        print(" The client asks each server itself.  (iterative queries, RD=0, no cache)")
    print()

    step_no = 0
    for step in result["steps"]:
        if step["kind"] == "note":
            print(f"   >> {step['text']}")
            print()
            continue

        step_no += 1
        if step["kind"] == "cache":
            print(f" Step {step_no}: Found in the resolver's CACHE  (no server contacted, 0 ms)")
            if step["answers"]:
                values = ", ".join(f"{r['type']} {r['value']}" for r in step["answers"])
                print(f"         Cached : {values}")
            else:
                print(f"         Cached : {step['status']}")
        else:
            server = step["server"]
            print(f" Step {step_no}: {asker} -> {server.level} server  {server.name} ({server.ip})")
            print(f"         Asked : {step['name']}  {step['qtype']}")
            print(f"         Reply : {describe_reply(step['reply'], step['qtype'])}")
            print(f"         Delay : {step['delay']} ms")
        print()

    print(THIN)
    status = result["status"]
    if status == "FOUND":
        print(f" RESULT : FOUND ({len(result['answers'])} record(s))")
        print_answers(result["answers"])
    elif status == "NXDOMAIN":
        print(" RESULT : NXDOMAIN - this domain does not exist")
    elif status == "NODATA":
        print(f" RESULT : NO DATA - the name exists but has no {qtype} record")
    else:
        print(" RESULT : FAILED - could not resolve the name")

    delays = result["delays"]
    servers_asked = len(delays)
    if servers_asked == 0:
        print("\n TIME   : 0 ms  (answered completely from cache)")
    else:
        sum_text = " + ".join(str(d) for d in delays)
        print(f"\n TIME   : {sum_text} = {sum(delays)} ms   ({servers_asked} server(s) contacted)")
    print(LINE)


def ask(prompt, default=""):
    value = input(prompt).strip()
    return value if value else default


def ask_type():
    qtype = ask("Record type (A, AAAA, CNAME, MX, NS, TXT, SOA, PTR) [A]: ", "A").upper()
    if qtype not in RECORD_TYPES:
        print(f"  '{qtype}' is not supported. Using A.")
        qtype = "A"
    return qtype


def resolve_menu(resolver, mode):
    name = ask("Domain name (e.g. www.example.com): ")
    if not name:
        print("  Please type a domain name.")
        return
    qtype = ask_type()
    result = resolver.resolve(name, qtype, mode)
    print_result(name, qtype, mode, result)


def reverse_menu(resolver):
    ip = ask("IP address (e.g. 203.0.113.10): ")
    try:
        reverse_name = ipaddress.ip_address(ip).reverse_pointer
    except ValueError:
        print("  That is not a valid IP address.")
        return
    print(f"\n  {ip} is looked up as the name: {reverse_name}")
    result = resolver.resolve(reverse_name, "PTR", "recursive")
    print_result(reverse_name, "PTR", "recursive", result)


def show_hierarchy(resolver):
    """Draw the zones as a tree. A zone's parent is the closest zone above it."""
    def parent_of(zone):
        while zone != ".":
            zone = zone.split(".", 1)[1] if "." in zone else "."
            if zone in ZONES:
                return zone
        return "."

    def server_for(zone):
        for s in resolver.servers:
            if zone in s.zones:
                return s
        return None

    def draw(zone, prefix, is_last, is_root):
        s = server_for(zone)
        if s is None:
            return
        label = ". (root)" if zone == "." else zone
        info = f"{s.name}  [{s.level}]  queries: {s.queries_received}"
        if is_root:
            left = " " + label
            child_prefix = " "
        else:
            branch = "└── " if is_last else "├── "
            left = prefix + branch + label
            child_prefix = prefix + ("    " if is_last else "│   ")
        print(f"{left:<36}{info}")
        children = sorted(z for z in ZONES if z != "." and parent_of(z) == zone)
        for i, child in enumerate(children):
            draw(child, child_prefix, i == len(children) - 1, False)

    print()
    print(LINE)
    print(" DNS HIERARCHY  (zone  ->  server in charge)")
    print(LINE)
    draw(".", "", True, True)
    print(LINE)


def show_cache(resolver):
    rows = resolver.cache_entries()
    print()
    print(LINE)
    print(" RESOLVER CACHE")
    print(LINE)
    if not rows:
        print(" (empty)")
    for name, qtype, status, answers, left in rows:
        if answers:
            values = ", ".join(r["value"] for r in answers)
        else:
            values = status
        print(f" {name:<30}{qtype:<6} expires in {left:>5}s   {values}")
    print(LINE)


def show_record_types():
    print()
    print(LINE)
    print(" DNS RECORD TYPES")
    print(LINE)
    for rtype, text in RECORD_TYPES.items():
        print(f" {rtype:<6} {text}")
    print(LINE)


def run_demo(resolver):
    """Runs several queries and prints a summary table - good for a quick presentation."""
    queries = [
        ("www.example.com", "A"),
        ("www.example.com", "A"),          # same again -> comes from cache
        ("example.com", "AAAA"),
        ("example.com", "MX"),
        ("example.com", "NS"),
        ("example.com", "SOA"),
        ("openwiki.org", "TXT"),
        ("www.shopkart.com", "A"),         # alias chain into another zone
        ("university.ac.in", "MX"),
        ("10.113.0.203.in-addr.arpa", "PTR"),
        ("nothing.example.com", "A"),      # does not exist
        ("ftp.example.com", "AAAA"),       # exists, but no IPv6
    ]
    resolver.clear_cache()
    print()
    print(LINE)
    print(" DEMO - recursive queries (cache cleared first)")
    print(LINE)
    print(f" {'QUERY':<28}{'TYPE':<6}{'RESULT':<10}{'SERVERS':<9}{'TIME':<8}ANSWER")
    print(" " + "-" * 90)
    for name, qtype in queries:
        result = resolver.resolve(name, qtype, "recursive")
        final = [r["value"] for r in result["answers"] if r["type"] == qtype]
        answer = ", ".join(final) if final else "-"
        delays = result["delays"]
        print(f" {name:<28}{qtype:<6}{result['status']:<10}{len(delays):<9}"
              f"{str(sum(delays)) + ' ms':<8}{answer}")
    print()
    print(" Notice: the 2nd 'www.example.com' took 0 ms because it came from the cache.")
    print(LINE)


# ======================================================================
# Main menu
# ======================================================================

MENU = """
================ DNS RESOLVER SIMULATION ================
 1. Resolve a domain  (RECURSIVE query - uses cache)
 2. Resolve a domain  (ITERATIVE query - step by step, no cache)
 3. Reverse lookup    (IP address -> name)
 4. Show DNS hierarchy
 5. Show cache
 6. Clear cache
 7. Run demo (all record types)
 8. Explain record types
 0. Exit
========================================================="""


def main():
    resolver = Resolver()
    while True:
        print(MENU)
        choice = ask("Choose an option: ")
        if choice == "1":
            resolve_menu(resolver, "recursive")
        elif choice == "2":
            resolve_menu(resolver, "iterative")
        elif choice == "3":
            reverse_menu(resolver)
        elif choice == "4":
            show_hierarchy(resolver)
        elif choice == "5":
            show_cache(resolver)
        elif choice == "6":
            resolver.clear_cache()
            print("\n  Cache cleared.")
        elif choice == "7":
            run_demo(resolver)
        elif choice == "8":
            show_record_types()
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("  Please choose a number from the menu.")
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")

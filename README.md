# DNS Resolver Simulation (simple version)

A terminal program that resolves domain names using a **mock DNS hierarchy** and shows each step:

```
Root server  ->  TLD server (.com)  ->  Authoritative server (example.com)
```

Plain Python only: no libraries to install, no web browser, no internet needed.

## How to run (VS Code)

1. **File → Open Folder…** and choose the `dns-resolver-simple` folder.
2. If VS Code shows **Restricted Mode**, click it and choose **Trust**.
3. Open `main.py` and click the **▶ Run** button (top right).
   You can also open **Terminal → New Terminal** and type `python3 main.py`.
4. Type a number from the menu and press Enter.

```
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
=========================================================
```

## Files

| File | What it does |
|---|---|
| `main.py` | The menu and all the printing. **Run this file.** |
| `resolver.py` | The resolver: walks Root → TLD → Authoritative, follows aliases, keeps the cache |
| `dns_server.py` | A mock name server: replies ANSWER, REFERRAL, NXDOMAIN or NODATA |
| `dns_data.py` | All servers and DNS records (edit this to add your own domains) |

## Concepts shown

- **DNS hierarchy:** root, top-level domain (TLD) and authoritative servers
- **Recursive vs iterative queries:** option 1 vs option 2
- **Referrals and glue records:** "Not me, ask this server at this IP"
- **Record types:** A, AAAA, CNAME, MX, NS, TXT, SOA, PTR
- **CNAME chains:** `www.shopkart.com` → `cdn.shopkart.com` → `shopkart.edge.cloudhost.net`
- **Reverse DNS:** `203.0.113.10` → `10.113.0.203.in-addr.arpa` → `example.com`
- **Caching and TTL:** repeat a query and it takes 0 ms instead of 75 ms
- **Errors:** NXDOMAIN (name doesn't exist) and NODATA (name exists, type doesn't)

## Example queries to try

| Name | Type | What it shows |
|---|---|---|
| `www.example.com` | A | Full walk root → .com → example.com; alias in the same zone |
| `www.example.com` | A (again) | Answered from the cache, 0 ms |
| `www.shopkart.com` | A | Alias chain that jumps to another domain (6 steps) |
| `example.com` | MX | Mail servers |
| `openwiki.org` | TXT | Text record under .org |
| `university.ac.in` | MX | The .in TLD |
| `nothing.example.com` | A | NXDOMAIN |
| `ftp.example.com` | AAAA | NODATA |
| `203.0.113.10` (option 3) | PTR | Reverse lookup |

## How the timing works (worked example)

Each server has a fake network delay: Root = 40 ms, TLD = 25 ms, Authoritative = 10 ms.

- 1st lookup of `www.example.com`: 40 + 25 + 10 = **75 ms** (3 servers)
- 2nd lookup (from cache): **0 ms** (0 servers)
- `www.shopkart.com` (alias into another zone): 75 + 75 = **150 ms** (6 servers)

## How to add a domain

In `dns_data.py`:

1. Add a server to `SERVERS`:
   ```python
   ("ns1.mysite.com", "198.51.100.77", "Authoritative", ["mysite.com"]),
   ```
2. Tell the `.com` zone where to find it (a delegation plus glue):
   ```python
   ("mysite.com",     "NS", "ns1.mysite.com", 172800),
   ("ns1.mysite.com", "A",  "198.51.100.77",  172800),
   ```
3. Add the zone with its records:
   ```python
   "mysite.com": [
       ("mysite.com",     "A",     "198.51.100.78", 300),
       ("www.mysite.com", "CNAME", "mysite.com",    300),
   ],
   ```

All IP addresses are made up. Most come from the ranges reserved for documentation (`192.0.2.x`, `198.51.100.x`, `203.0.113.x`).

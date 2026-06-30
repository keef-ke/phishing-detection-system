
"""
04_whois_dns_test.py
Test that python-whois and dnspython work correctly.
Run: python notebooks/04_whois_dns_test.py
"""
import datetime

# Test WHOIS
print("="*55)
print("TESTING: python-whois")
print("="*55)
try:
    import whois

    test_domains = ['google.com', 'github.com']
    for domain in test_domains:
        print(f"\nDomain: {domain}")
        try:
            w = whois.whois(domain)
            creation = w.creation_date
            if isinstance(creation, list): creation = creation[0]
            expiry = w.expiration_date
            if isinstance(expiry, list): expiry = expiry[0]

            if creation and isinstance(creation, datetime.datetime):
                age = (datetime.date.today() - creation.date()).days
                print(f"  Creation date : {creation.date()}")
                print(f"  Domain age    : {age} days")
            if expiry:
                print(f"  Expiry date   : {expiry}")
            print(f"  Registrar     : {w.registrar}")
            print("  ✅ WHOIS OK")
        except Exception as e:
            print(f"  ❌ WHOIS Error: {e}")
except ImportError:
    print("❌ python-whois not installed. Run: pip install python-whois")


# Test DNS
print("\n" + "="*55)
print("TESTING: dnspython")
print("="*55)
try:
    import dns.resolver

    test_domains = ['google.com', 'github.com']
    for domain in test_domains:
        print(f"\nDomain: {domain}")
        try:
            # A record
            a_records = dns.resolver.resolve(domain, 'A')
            ips = [r.to_text() for r in a_records]
            print(f"  A records  : {ips[:3]}")
            print(f"  TTL        : {a_records.rrset.ttl} seconds")
        except Exception as e:
            print(f"  A record error: {e}")

        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            print(f"  MX records : {len(list(mx_records))} found")
        except Exception as e:
            print(f"  MX error   : {e}")

        try:
            ns_records = dns.resolver.resolve(domain, 'NS')
            print(f"  NS count   : {len(list(ns_records))}")
        except Exception as e:
            print(f"  NS error   : {e}")
        print("  ✅ DNS OK")

except ImportError:
    print("❌ dnspython not installed. Run: pip install dnspython")

print("\n✅ Test complete.")
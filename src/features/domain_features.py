"""
domain_features.py  —  Domain / WHOIS / DNS / SSL Feature Extractor
Optimized with standard socket timeouts and single-pass WHOIS lookups.
Saved at: src/features/domain_features.py
"""
import socket
import ssl
import datetime
from urllib.parse import urlparse

# Set global timeout to stop lingering socket blocks after 5 seconds
socket.setdefaulttimeout(5)

try:
    import whois
except ImportError:
    whois = None

try:
    import dns.resolver
except ImportError:
    dns = None


def _domain(url):
    try:
        host = urlparse(url).netloc.split(':')[0].lower()
        return host[4:] if host.startswith('www.') else host
    except Exception: 
        return None


def _days(date_obj):
    if isinstance(date_obj, list): date_obj = date_obj[0]
    if date_obj is None: return -1
    if isinstance(date_obj, datetime.datetime): date_obj = date_obj.date()
    return (datetime.date.today() - date_obj).days


# ── Optimized Single-Pass WHOIS Logic ──────────────────────────────────────────

def _get_whois(domain):
    """Single WHOIS lookup, reused across all domain age features."""
    if not whois or not domain:
        return None
    try:
        return whois.whois(domain)
    except Exception:
        return None


def get_domain_age_days(w):
    if w is None: return -1
    return _days(w.creation_date)


def get_domain_expiry_days(w):
    if w is None: return -1
    try:
        exp = w.expiration_date
        if isinstance(exp, list): exp = exp[0]
        if exp is None: return -1
        if isinstance(exp, datetime.datetime): exp = exp.date()
        return (exp - datetime.date.today()).days
    except Exception:
        return -1


def get_registration_length_days(w):
    if w is None: return -1
    try:
        c, e = w.creation_date, w.expiration_date
        if isinstance(c, list): c = c[0]
        if isinstance(e, list): e = e[0]
        if not c or not e: return -1
        if isinstance(c, datetime.datetime): c = c.date()
        if isinstance(e, datetime.datetime): e = e.date()
        return (e - c).days
    except Exception:
        return -1


# ── DNS & SSL Feature Extractors ──────────────────────────────────────────────

def has_dns_a_record(url):
    d = _domain(url)
    if not d: return -1
    if dns:
        try: dns.resolver.resolve(d, 'A'); return 1
        except: return 0
    else:
        try: socket.gethostbyname(d); return 1
        except: return 0


def has_dns_mx_record(url):
    if dns is None: return -1
    d = _domain(url)
    if not d: return -1
    try: dns.resolver.resolve(d, 'MX'); return 1
    except: return 0


def count_dns_nameservers(url):
    if dns is None: return -1
    d = _domain(url)
    if not d: return -1
    try: return len(list(dns.resolver.resolve(d, 'NS')))
    except: return -1


def get_dns_ttl(url):
    if dns is None: return -1
    d = _domain(url)
    if not d: return -1
    try:
        ans = dns.resolver.resolve(d, 'A')
        return ans.rrset.ttl if ans.rrset else -1
    except: return -1


def get_ssl_expiry_days(url):
    d = _domain(url)
    if not d: return -1
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((d, 443), timeout=5) as s:
            with ctx.wrap_socket(s, server_hostname=d) as ssock:
                cert = ssock.getpeercert()
        not_after = cert.get('notAfter','')
        exp = datetime.datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z').date()
        return (exp - datetime.date.today()).days
    except: return -1


def has_valid_ssl(url):
    return 1 if get_ssl_expiry_days(url) > 0 else 0


# ── Unified Domain Master Map ──────────────────────────────────────────────────

def extract_domain_features(url):
    domain = _domain(url)
    w = _get_whois(domain)  # Performs ONE network query rather than three
    
    return {
        'domain_age_days':          get_domain_age_days(w),
        'domain_expiry_days':       get_domain_expiry_days(w),
        'registration_length_days': get_registration_length_days(w),
        'has_dns_a_record':         has_dns_a_record(url),
        'has_dns_mx_record':        has_dns_mx_record(url),
        'dns_nameserver_count':     count_dns_nameservers(url),
        'dns_ttl':                  get_dns_ttl(url),
        'ssl_expiry_days':          get_ssl_expiry_days(url),
        'has_valid_ssl':            has_valid_ssl(url),
    }


if __name__ == '__main__':
    url = 'https://www.github.com'
    print(f"Domain features for: {url}")
    for k, v in extract_domain_features(url).items():
        print(f"  {k:<30}: {v}")
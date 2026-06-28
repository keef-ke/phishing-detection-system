# Feature Engineering Plan
## Layer 1: URL Lexical Features (no network needed, instantaneous)
| # | Feature Name | Type | Description |
|---|-------------|------|-------------|
| 1 | url_length | int | Total URL character count |
| 2 | domain_length | int | Domain character count |
| 3 | num_dots | int | Number of '.' in URL |
| 4 | num_hyphens | int | Number of '-' in URL |
| 5 | num_at_symbols | int | Number of '@' symbols |
| 6 | num_question_marks | int | Number of '?' |
| 7 | num_slashes | int | Number of '/' |
| 8 | num_percent_encoding | int | Number of '%' (obfuscation) |
| 9 | num_digits | int | Total digit count |
| 10 | num_subdomains | int | Subdomain depth count |
| 11 | has_https | binary | 1=HTTPS, 0=HTTP |
| 12 | is_ip_address | binary | 1 if hostname is raw IP |
| 13 | url_shortener_used | binary | Known shortener detected |
| 14 | suspicious_keyword_cnt | int | Count of phishing keywords |
| 15 | digit_ratio | float | digits / URL length |
| 16 | special_char_ratio | float | special chars / URL length |
| 17 | double_slash_in_path | binary | // in path |
| 18 | num_ampersands | int | Count of & |
| 19 | path_length | int | Length of URL path |
| 20 | has_non_std_port | binary | Non-80/443 port |
| 21 | query_length | int | Length of query string |
| 22 | num_equal_signs | int | Count of = |

## Layer 2: Domain/WHOIS/DNS Features (network, ~2-5 sec each)
| # | Feature Name | Type | Description |
|---|-------------|------|-------------|
| 23 | domain_age_days | int | Days since registration |
| 24 | domain_expiry_days | int | Days until expiry |
| 25 | registration_length_days | int | Planned domain lifetime |
| 26 | has_dns_a_record | binary | A record exists |
| 27 | has_dns_mx_record | binary | MX record exists |
| 28 | dns_nameserver_count | int | Number of NS records |
| 29 | dns_ttl | int | TTL value in seconds |
| 30 | ssl_expiry_days | int | SSL cert days remaining |
| 31 | has_valid_ssl | binary | SSL valid and not expired |

## Layer 3: Webpage HTML Features (fetch page, ~3-10 sec each)
| # | Feature Name | Type | Description |
|---|-------------|------|-------------|
| 32 | http_status_code | int | HTTP response code |
| 33 | redirect_count | int | Number of HTTP redirects |
| 34 | response_time_ms | int | Server response time (ms) |
| 35 | has_login_form | binary | Password input form found |
| 36 | external_links_ratio | float | External links / total links |
| 37 | favicon_external | binary | Favicon from foreign domain |
| 38 | right_click_disabled | binary | JS disables right-click |
| 39 | has_popup_windows | binary | window.open() detected |
| 40 | has_hidden_iframe | binary | Invisible iframe found |
| 41 | empty_anchor_ratio | float | Empty href anchors / total |
| 42 | meta_refresh_redirect | binary | Meta refresh tag found |
| 43 | form_action_external | binary | Form posts to other domain |

## TOTAL: 43 features
#!/usr/bin/env python3
"""
websearch.py — local replacement for the disabled WebSearch tool.

Why this exists: this Claude Code session runs through a Databricks AI Gateway
routed to Anthropic-on-Bedrock. Anthropic's first-party `web_search` server tool
does not exist on Bedrock, so every WebSearch call returns HTTP 400 BAD_REQUEST.
Plain messages and client-side WebFetch work fine. This script restores search by
querying search-engine HTML endpoints directly and returning clean results.

KEY INSIGHT (verified 2026-07): the fix for non-English coverage is the QUERY
LANGUAGE, not the engine. DDG indexes Cyrillic/Chinese/etc. fine — a Russian-
language DDG query surfaces tadviser.ru and sberbank.ru primary sources; a
Chinese query surfaces .cn bank sources. Search in the TARGET LANGUAGE.

Engines:
    ddg    (default) DuckDuckGo — workhorse for ALL languages when you query
           in the target language (RU/CN/JP queries return native sources).
    baidu  Baidu     — bonus depth for Chinese (.cn sources DDG ranks lower). Works.
    yandex Yandex     — UNREACHABLE from this environment (hosts refuse connection,
           HTTP 000). Kept for completeness; use DDG-in-Russian instead.

Usage:
    python3 websearch.py "query terms"                      # DDG, 10 results
    python3 websearch.py -n 20 "query terms"                # N results
    python3 websearch.py --engine baidu "查询词"             # Baidu (Chinese)
    python3 websearch.py --engine yandex "запрос"           # Yandex (Russian)
    python3 websearch.py --json "query terms"               # JSON out

Note: Baidu/Yandex HTML endpoints are captcha-prone and less reliable than DDG.
If an engine returns 0 results it may be blocked — the tool says so rather than
failing silently. Pair with WebFetch to read the actual source pages.
"""
import sys, re, json, html, urllib.parse, urllib.request

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

import time

def fetch(url, data=None, headers=None, retries=3):
    h = {"User-Agent": UA, "Accept-Language": "en,zh,ru;q=0.8"}
    if headers:
        h.update(headers)
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=data, headers=h)
            with urllib.request.urlopen(req, timeout=20) as r:
                raw = r.read()
            for enc in ("utf-8", "gbk", "latin-1"):
                try:
                    return raw.decode(enc)
                except Exception:
                    continue
            return raw.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            last = e
            # 202/429/403 = soft rate-limit → back off and retry
            if e.code in (202, 403, 429) and attempt < retries - 1:
                time.sleep(3 * (attempt + 1))
                continue
            raise
        except Exception as e:
            last = e
            if attempt < retries - 1:
                time.sleep(2)
                continue
            raise
    if last:
        raise last

def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()

# ---------------- DuckDuckGo (Western / English) ----------------
def unwrap_ddg(href):
    m = re.search(r"[?&]uddg=([^&]+)", href)
    if m:
        return urllib.parse.unquote(m.group(1))
    if href.startswith("//"):
        return "https:" + href
    return href

def search_ddg(query, n=10):
    body = urllib.parse.urlencode({"q": query}).encode()
    page = fetch("https://html.duckduckgo.com/html/", data=body)
    results = []
    for m in re.finditer(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', page, re.S):
        url = unwrap_ddg(html.unescape(m.group(1)))
        title = strip_tags(m.group(2))
        if url.startswith("http") and title:
            results.append({"title": title, "url": url, "snippet": ""})
        if len(results) >= n:
            break
    snips = [strip_tags(s) for s in re.findall(r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>', page, re.S)]
    for i, s in enumerate(snips):
        if i < len(results):
            results[i]["snippet"] = s
    return results

# ---------------- Baidu (Chinese) ----------------
def search_baidu(query, n=10):
    # Baidu web search HTML endpoint. Result links are redirect wrappers
    # (baidu.com/link?url=...) that resolve to the real URL on fetch — we
    # return them as-is; WebFetch follows the redirect.
    url = "https://www.baidu.com/s?" + urllib.parse.urlencode({"wd": query, "rn": max(n, 10)})
    page = fetch(url, headers={"Referer": "https://www.baidu.com/"})
    if "验证码" in page or "百度安全验证" in page:
        return {"_blocked": "baidu returned a captcha/security page"}
    results = []
    # Baidu result blocks: <h3 class="t"...><a href="...">title</a></h3>
    for m in re.finditer(r'<h3[^>]*class="[^"]*t[^"]*"[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', page, re.S):
        u = html.unescape(m.group(1))
        title = strip_tags(m.group(2))
        if u.startswith("http") and title:
            results.append({"title": title, "url": u, "snippet": ""})
        if len(results) >= n:
            break
    return results

# ---------------- Yandex (Russian) ----------------
def search_yandex(query, n=10):
    url = "https://yandex.com/search/?" + urllib.parse.urlencode({"text": query})
    page = fetch(url)
    if "captcha" in page.lower() or "showcaptcha" in page.lower() or "are you a robot" in page.lower():
        return {"_blocked": "yandex returned a captcha page"}
    results = []
    # Yandex organic links carry class markers; grab external hrefs from result titles
    for m in re.finditer(r'<a[^>]+class="[^"]*(?:OrganicTitle-Link|Link_theme_normal|organic__url)[^"]*"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', page, re.S):
        u = html.unescape(m.group(1))
        title = strip_tags(m.group(2))
        if u.startswith("http") and title:
            results.append({"title": title, "url": u, "snippet": ""})
        if len(results) >= n:
            break
    if not results:
        return {"_blocked": "yandex returned no parseable results (likely JS-rendered or blocked)"}
    return results

# ---------------- Bing (RESILIENT — proven to survive when DDG gets rate-blocked) ----------------
# DDG's HTML endpoint returns bot-detection ("anomaly / cc=botnet") pages under heavy
# parallel load. Bing held up during the sweep and surfaces native-language sources well
# via the mkt locale param. Use --mkt ru-RU / fr-FR / de-DE / ja-JP / zh-CN etc.
def search_bing(query, n=10, mkt=None):
    params = {"q": query}
    if mkt:
        params["mkt"] = mkt
    url = "https://www.bing.com/search?" + urllib.parse.urlencode(params)
    page = fetch(url, headers={"Referer": "https://www.bing.com/"})
    results = []
    # Bing organic results: <li class="b_algo"> ... <h2><a href="URL">title</a></h2> ... <p>snippet</p>
    for block in re.findall(r'<li class="b_algo".*?</li>', page, re.S):
        m = re.search(r'<h2>.*?<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', block, re.S)
        if not m:
            continue
        u = html.unescape(m.group(1)); title = strip_tags(m.group(2))
        sn = re.search(r'<p[^>]*>(.*?)</p>', block, re.S)
        snippet = strip_tags(sn.group(1)) if sn else ""
        if u.startswith("http") and title:
            results.append({"title": title, "url": u, "snippet": snippet})
        if len(results) >= n:
            break
    if not results:
        return {"_blocked": "bing returned no parseable results (captcha or markup change)"}
    return results

ENGINES = {"ddg": search_ddg, "baidu": search_baidu, "yandex": search_yandex, "bing": search_bing}

def main():
    args = sys.argv[1:]
    n, as_json, engine, mkt = 10, False, "ddg", None
    out = []
    i = 0
    while i < len(args):
        if args[i] in ("-n", "--num"):
            n = int(args[i+1]); i += 2
        elif args[i] in ("-e", "--engine"):
            engine = args[i+1].lower(); i += 2
        elif args[i] == "--mkt":
            mkt = args[i+1]; i += 2
        elif args[i] == "--json":
            as_json = True; i += 1
        else:
            out.append(args[i]); i += 1
    if not out:
        print("usage: websearch.py [-n N] [--engine ddg|baidu|yandex] [--json] <query>", file=sys.stderr)
        sys.exit(2)
    if engine not in ENGINES:
        print(f"unknown engine '{engine}' (use: ddg, baidu, yandex)", file=sys.stderr); sys.exit(2)
    query = " ".join(out)
    try:
        res = ENGINES[engine](query, n, mkt) if engine == "bing" else ENGINES[engine](query, n)
    except Exception as ex:
        print(json.dumps({"_error": f"{engine} fetch failed: {ex}"}) if as_json
              else f"[{engine}] fetch failed: {ex}", file=sys.stderr)
        sys.exit(1)
    # engine returned a block/diagnostic dict instead of a list
    if isinstance(res, dict):
        msg = res.get("_blocked") or res.get("_error") or "no results"
        print(json.dumps(res, ensure_ascii=False, indent=2) if as_json else f"[{engine}] {msg}")
        return
    if as_json:
        print(json.dumps(res, ensure_ascii=False, indent=2)); return
    print(f"[{engine}] {len(res)} results for: {query}\n")
    for k, r in enumerate(res, 1):
        print(f"{k}. {r['title']}\n   {r['url']}")
        if r["snippet"]:
            print(f"   {r['snippet']}")
        print()

if __name__ == "__main__":
    main()

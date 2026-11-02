"""Sim racing akciófigyelő: Shopify-boltok /products.json adatából árelőzményt épít,
és csak a valóban esett árakat dobja fel. Kimenet: docs/index.html + docs/deals.json."""
import json, statistics, urllib.request, datetime, pathlib, html

ROOT = pathlib.Path(__file__).parent
CFG = json.loads((ROOT / "shops.json").read_text())
HIST_FILE, OUT = ROOT / "history.json", ROOT / "docs"
UA = {"User-Agent": "Mozilla/5.0 (personal price watcher)"}
TODAY = datetime.date.today().isoformat()
THR = CFG.get("threshold_percent", 15) / 100


def fetch_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return json.load(r)


def fetch_shop(shop):
    items = []
    for page in range(1, 9):
        prods = fetch_json(f"https://{shop['domain']}/products.json?limit=250&page={page}").get("products", [])
        if not prods:
            break
        for p in prods:
            vs = [v for v in p.get("variants", []) if v.get("available", True) and float(v["price"]) > 0]
            if not vs:
                continue
            v = min(vs, key=lambda x: float(x["price"]))
            cmp_ = float(v["compare_at_price"]) if v.get("compare_at_price") else None
            items.append({
                "key": f"{shop['domain']}/{p['handle']}", "name": p["title"], "shop": shop["name"],
                "cur": shop["currency"], "price": float(v["price"]), "cmp": cmp_,
                "url": f"https://{shop['domain']}/products/{p['handle']}",
                "img": (p.get("images") or [{}])[0].get("src", ""),
            })
    return items


def analyse(hist, it):
    prev = [p for d, p in hist if d < TODAY]
    price, cmp_ = it["price"], it["cmp"]
    claim = (1 - price / cmp_) if cmp_ and cmp_ > price else 0
    if len(prev) < 3:  # még kevés előzmény: csak a bolt saját jelölése
        return ("claim", claim, None) if claim >= 0.10 else (None, 0, None)
    base, low = statistics.median(prev), min(prev)
    disc = 1 - price / base
    if disc >= THR and price <= low:
        return "real", disc, base
    if disc >= THR / 2:
        return "mild", disc, base
    if cmp_ and cmp_ > base * 1.15 and claim >= 0.10:
        return "fake", claim, base
    return None, disc, base


def main():
    try:
        hist = json.loads(HIST_FILE.read_text())
    except Exception:
        hist = {}
    deals, errors = [], []
    for shop in CFG["shops"]:
        try:
            items = fetch_shop(shop)
        except Exception as e:
            errors.append(f"{shop['name']}: {e}")
            continue
        for it in items:
            h = hist.setdefault(it["key"], [])
            status, pct, base = analyse(h, it)
            if not h or h[-1][0] != TODAY:
                h.append([TODAY, it["price"]])
            else:
                h[-1][1] = it["price"]
            del h[:-120]
            if status:
                deals.append({**it, "status": status, "pct": round(pct * 100), "base": base, "n": len(h)})
    HIST_FILE.write_text(json.dumps(hist))
    order = {"real": 0, "mild": 1, "claim": 2, "fake": 3}
    deals.sort(key=lambda d: (order[d["status"]], -d["pct"]))
    OUT.mkdir(exist_ok=True)
    (OUT / "deals.json").write_text(json.dumps(deals, ensure_ascii=False, indent=1))
    (OUT / "index.html").write_text(render(deals, errors), encoding="utf-8")
    print(f"{len(deals)} találat, {len(errors)} hiba")


LABEL = {"real": "Valódi akció", "mild": "Mérsékelt", "claim": "Bolti jelölés, előzmény még nincs", "fake": "Gyanús „régi ár”"}


def money(v, c):
    return f"{v:,.0f} {c}".replace(",", " ") if c == "HUF" else f"{v:,.2f} {c}"


def render(deals, errors):
    cards = []
    for d in deals:
        ref = f"szokásos: {money(d['base'], d['cur'])} ({d['n']} nap adat)" if d["base"] else (f"áthúzott: {money(d['cmp'], d['cur'])}" if d["cmp"] else "")
        img = f'<img src="{html.escape(d["img"])}" alt="" loading="lazy">' if d["img"] else "<i></i>"
        cards.append(
            f'<a class="c {d["status"]}" data-s="{d["status"]}" href="{html.escape(d["url"])}" target="_blank" rel="noopener">{img}'
            f'<div><b>{html.escape(d["name"])}</b><span>{html.escape(d["shop"])}</span>'
            f'<em>{LABEL[d["status"]]}</em><small>{ref}</small></div>'
            f'<div class="p"><strong>{"−" if d["status"] != "fake" else ""}{d["pct"]}%</strong>{money(d["price"], d["cur"])}</div></a>')
    err = f'<p class="e">Nem elérhető: {html.escape("; ".join(errors))}</p>' if errors else ""
    return PAGE.replace("%%CARDS%%", "\n".join(cards) or "<p>Ma még nincs találat.</p>").replace(
        "%%ERR%%", err).replace("%%TS%%", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))


PAGE = """<!DOCTYPE html><html lang="hu"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sim racing akciók</title><style>
:root{color-scheme:light dark;--bg:#eceef1;--cd:#fff;--ink:#14181f;--mut:#5d6674;--ln:#d5d9e0;--g:#0a7d4a;--m:#8a5a00;--b:#b3261e}
@media(prefers-color-scheme:dark){:root{--bg:#12151a;--cd:#1b2028;--ink:#eef1f5;--mut:#9aa4b3;--ln:#2c3440;--g:#4fd68e;--m:#f0b94a;--b:#ff8a80}}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,sans-serif}main{max-width:900px;margin:0 auto;padding:20px 14px}
h1{margin:0 0 4px}.t{color:var(--mut);margin:0 0 14px}select{font:inherit;padding:6px;margin-bottom:12px}
.c{display:grid;grid-template-columns:72px 1fr auto;gap:12px;align-items:center;background:var(--cd);border:1px solid var(--ln);border-left:6px solid var(--ln);border-radius:8px;padding:10px 12px;margin-bottom:8px;color:inherit;text-decoration:none}
.c.real{border-left-color:var(--g)}.c.mild,.c.claim{border-left-color:var(--m)}.c.fake{border-left-color:var(--b)}
.c img,.c i{width:72px;height:56px;object-fit:contain}.c b{display:block}.c span,.c small{color:var(--mut);display:block;font-size:13px}.c em{font-style:normal;font-size:13px}
.real em{color:var(--g)}.mild em,.claim em{color:var(--m)}.fake em{color:var(--b)}.p{text-align:right}.p strong{display:block;font-size:24px}.e{color:var(--b)}
</style></head><body><main><h1>Sim racing akciók</h1><p class="t">Frissítve: %%TS%%</p>
<select id="f"><option value="">Minden találat</option><option value="real">Csak valódi akciók</option></select>
%%CARDS%%%%ERR%%</main><script>document.getElementById("f").onchange=function(){var v=this.value;document.querySelectorAll(".c").forEach(function(c){c.style.display=!v||c.dataset.s===v?"":"none"})}</script></body></html>"""

if __name__ == "__main__":
    main()

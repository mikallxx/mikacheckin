"""Build the production site for mikatravel.com from index.html (preview source).

Output: dist/
  index.html            home
  <post-id>/index.html  one page per accommodation (pre-rendered for Google)
  404.html, sitemap.xml, robots.txt, favicon.svg, img/...
"""
import json, os, re, shutil, subprocess, sys, time, html
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DOMAIN = "https://mikacheckin.com"
SRC = os.path.join(ROOT, "source", "index.html")
DIST = os.path.join(ROOT, "dist")
SITE_NAME = "Mika Check-in｜今晚住這裡"
HOME_DESC = "Mika 的住宿開箱攻略：看完 IG 影片，在這裡看房型、價位、周邊美食景點和專屬優惠。"

# posts that are live (title / description / cover for share previews)
POSTS = [
    {
        "id": "hangwang",
        "title": "巷往 Villa｜宜蘭冬山獨棟庭園渡假別墅，8～22 人入住，一樓孝親房、二樓檜木房",
        "desc": "宜蘭冬山包棟民宿巷往 Villa 入住心得：一樓兩間雙人房帶長輩好安排、二樓檜木四人房、三樓六人房，KTV、麻將、戲水池，附 Mika 專屬折扣碼。",
        "image": "img/hangwang/01.jpg",
    },
]

FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><circle cx="32" cy="32" r="32" fill="#274B9B"/><text x="32" y="43" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-weight="700" font-size="32" fill="#fff">M</text></svg>"""


def head_block(title, desc, url, image, page_post=None, noindex=False):
    t, d = html.escape(title), html.escape(desc)
    js = "window.SITE_PROD=true;" + (f'window.PAGE_POST={json.dumps(page_post)};' if page_post else "")
    return f"""<base href="/">
<title>{t}</title>
<meta name="description" content="{d}">
<link rel="canonical" href="{url}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<meta property="og:type" content="{'article' if page_post else 'website'}">
<meta property="og:site_name" content="{html.escape(SITE_NAME)}">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{DOMAIN}/{image}">
<meta name="twitter:card" content="summary_large_image">
{'<meta name="robots" content="noindex">' if noindex else ''}
<style>.preview-only{{display:none!important}}</style>
<script>{js}</script>"""


def make_page(src, **kw):
    s = re.sub(r"<title>.*?</title>", "", src, count=1, flags=re.S)
    return s.replace('<meta name="viewport"', head_block(**kw) + '\n<meta name="viewport"', 1)


def main():
    subprocess.run([sys.executable, os.path.join(ROOT, "source", "make_lqip.py")], check=True)
    src = open(SRC, encoding="utf-8").read()
    if os.path.exists(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST)
    # assets: only images actually referenced
    shutil.copytree(os.path.join(ROOT, "source", "img", "site"), f"{DIST}/img/site")
    for p in POSTS:
        shutil.copytree(os.path.join(ROOT, "source", "img", p["id"]), f"{DIST}/img/{p['id']}")
    open(f"{DIST}/favicon.svg", "w").write(FAVICON)

    home = make_page(src, title=SITE_NAME, desc=HOME_DESC, url=DOMAIN + "/", image="img/site/cover.jpg")
    open(f"{DIST}/index.html", "w", encoding="utf-8").write(home)
    open(f"{DIST}/404.html", "w", encoding="utf-8").write(
        make_page(src, title="找不到這個頁面｜" + SITE_NAME, desc=HOME_DESC, url=DOMAIN + "/",
                  image="img/site/cover.jpg", noindex=True))
    for p in POSTS:
        os.makedirs(f"{DIST}/{p['id']}")
        page = make_page(src, title=p["title"] + "｜Mika Check-in", desc=p["desc"],
                         url=f"{DOMAIN}/{p['id']}/", image=p["image"], page_post=p["id"])
        open(f"{DIST}/{p['id']}/index.html", "w", encoding="utf-8").write(page)

    # pre-render article HTML so it is in the page source (for Google / link previews)
    srv = subprocess.Popen([sys.executable, "-m", "http.server", "8765", "-d", DIST],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    try:
        ids = json.dumps([p["id"] for p in POSTS])
        out = subprocess.run(["node", "-e", f"""
const {{chromium}}=require('playwright');
(async()=>{{const b=await chromium.launch();const r={{}};
for(const id of {ids}){{const p=await b.newPage({{viewport:{{width:390,height:800}}}});await p.goto('http://localhost:8765/'+id+'/');await p.waitForTimeout(600);
 r[id]=await p.$eval('#article',e=>e.innerHTML);await p.close();}}
console.log(JSON.stringify(r));await b.close();}})();"""], capture_output=True, text=True, check=True)
        rendered = json.loads(out.stdout)
    finally:
        srv.terminate()
    for p in POSTS:
        f = f"{DIST}/{p['id']}/index.html"
        s = open(f, encoding="utf-8").read()
        s = s.replace('<article id="article"></article>', f'<article id="article">{rendered[p["id"]]}</article>', 1)
        s = s.replace("<body>", '<body class="reading">', 1)
        open(f, "w", encoding="utf-8").write(s)

    today = time.strftime("%Y-%m-%d")
    urls = [DOMAIN + "/"] + [f"{DOMAIN}/{p['id']}/" for p in POSTS]
    open(f"{DIST}/sitemap.xml", "w").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls) + "</urlset>\n")
    open(f"{DIST}/robots.txt", "w").write(f"User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n")
    n = sum(len(fs) for _, _, fs in os.walk(DIST))
    print("built", DIST, "files:", n)


if __name__ == "__main__":
    main()

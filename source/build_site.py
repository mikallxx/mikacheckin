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
        "id": "pabohou",
        "title": "帕鉑候工所｜高雄大港橋、駁二住宿，輕軌站就在附近",
        "desc": "位置在大港橋、駁二一帶，輕軌站就在附近，搭車移動很方便。",
        "image": "img/site/cover.jpg",
        "draft": True,
    },
    {
        "id": "xushu",
        "title": "旭樹。寓所｜台中東海商圈住宿，輸入折扣碼享 95 折",
        "desc": "就在台中東海商圈，輸入 Mika 專屬折扣碼享 95 折。",
        "image": "img/site/cover.jpg",
        "draft": True,
    },
    {
        "id": "yunxiu",
        "title": "雲岫海景渡假會館｜宜蘭海景包棟民宿，看得到龜山島，折扣碼享 65 折",
        "desc": "整棟五間房、最多住 14 人，看得到海景和龜山島，有 25 米海景泳池。輸入折扣碼享 65 折。",
        "image": "img/site/cover.jpg",
        "draft": True,
    },
    {
        "id": "paboshe",
        "title": "帕鉑舍旅｜高雄車站走路 3 分鐘，四人住一人不到 600 元",
        "desc": "距離高雄車站走路只要 3 分鐘，四人入住平均一人不到 600 元，公共空間免費提供咖啡和點心。",
        "image": "img/site/cover.jpg",
        "draft": True,
    },
    {
        "id": "yiqi",
        "title": "一期家旅｜台中住宿，大片落地窗、頂樓露台看夜景",
        "desc": "房間有大片落地窗，提供 Dyson 吹風機和茶籽堂備品，頂樓露台可以看夜景。",
        "image": "img/site/cover.jpg",
        "draft": True,
    },
    {
        "id": "hanyu",
        "title": "瀚寓酒店｜台北住宿，房間就能看到 101，附開放式廚房",
        "desc": "房間就能直接看到台北 101，空間寬敞還有開放式廚房，鄰近新光三越和捷運。",
        "image": "img/site/cover.jpg",
        "draft": True,
    },
    {
        "id": "yuguang",
        "title": "餘光民宿｜台南安平漁光島，榻榻米房、早餐喝牛肉湯",
        "desc": "一進門就是大片榻榻米，還能騎腳踏車去海邊看夕陽，隔天早餐喝得到台南牛肉湯。",
        "image": "img/site/cover.jpg",
        "draft": True,
    },
    {
        "id": "lvju",
        "title": "旅居文旅｜台中住宿，70 吋大電視、24 小時免費零食咖啡",
        "desc": "房間乾淨舒服，有 70 吋超大電視，大廳 24 小時有免費零食和咖啡。",
        "image": "img/site/cover.jpg",
        "draft": True,
    },
    {
        "id": "caosu",
        "title": "草宿 Auto 智旅｜南投草屯無人旅店，24 小時自助入住",
        "desc": "草屯市區新開幕的無人旅店，24 小時自助入住，很適合喜歡自在入住的 I 人。",
        "image": "img/site/cover.jpg",
        "draft": True,
    },
    {
        "id": "youli",
        "title": "有里日子露營區｜苗栗卓蘭免裝備露營，還能玩攀樹",
        "desc": "結合自然與冒險，可以體驗免裝備露營，還能參加刺激又安全的攀樹活動。",
        "image": "img/site/cover.jpg",
        "draft": True,
    },
    {
        "id": "r9",
        "title": "R9 貨櫃屋｜沖繩宇流麻市貨櫃屋飯店，乾淨安靜的獨立客房",
        "desc": "乾淨、安靜的獨立貨櫃屋客房，每天有人協助簡單打掃，適合自駕自由行。",
        "image": "img/site/cover.jpg",
        "draft": True,
    },
    {
        "id": "jinshi",
        "title": "金石新月光｜新北九份山城民宿，看山也看海，五種主題房",
        "desc": "有主人品味的山城民宿，一邊看山一邊看海，有停車場，開車約五分鐘到九份。",
        "image": "img/site/cover.jpg",
        "draft": True,
    },
    {
        "id": "hakuna",
        "title": "哈庫納馬塔塔｜宜蘭市包棟民宿，全台唯一非洲風格",
        "desc": "宜蘭市包棟民宿哈庫納馬塔塔，全台唯一非洲風格，附 Mika 開箱影片與專屬折扣碼。",
        "image": "img/site/cover.jpg",
        "draft": True,
    },
    {
        "id": "guipu",
        "title": "歸樸森活露營區｜嘉義懶人露營，免帶裝備、夕陽超美",
        "desc": "嘉義歸樸森活露營區入住心得：不用帶任何裝備的懶人營區，傍晚夕陽非常漂亮，附 Mika 開箱影片。",
        "image": "img/site/cover.jpg",
        "draft": True,
    },
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
    global POSTS
    POSTS = [p for p in POSTS if not p.get("draft")]
    subprocess.run([sys.executable, os.path.join(ROOT, "source", "make_lqip.py")], check=True)
    src = open(SRC, encoding="utf-8").read()
    if os.path.exists(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST)
    # assets: only images actually referenced
    shutil.copytree(os.path.join(ROOT, "source", "img", "site"), f"{DIST}/img/site")
    for p in POSTS:
        src_img = os.path.join(ROOT, "source", "img", p["id"])
        if os.path.isdir(src_img):
            shutil.copytree(src_img, f"{DIST}/img/{p['id']}")
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

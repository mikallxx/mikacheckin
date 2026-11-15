"""把住宿後台（Claude artifact 資料庫 `stays`）的資料寫進 index.html。

用法：python3 stays_to_posts.py stays.json
stays.json＝後台 db_list 的結果，格式為 [{"id": 文件 id, "data": {...}}, ...]

會改寫 index.html 中三段「後台產生」區塊：
  1. ALL_POSTS 裡一般住宿文章（巷往是手工版，只更新不覆蓋 render）
  2. deals 裡的折扣碼
  3. COPY_TEXTS 裡的詢問訊息、分享文案
"""
import json, re, sys, html, pathlib

ROOT = pathlib.Path(__file__).parent
SRC = ROOT / "index.html"
HANDMADE = {"hangwang": "renderHangwang"}   # 手工版文章：沿用自己的 render

def md(t):
    """後台標記 → HTML：**粗體**、[[紅字]]"""
    t = html.escape(str(t or "").strip(), quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\[\[(.+?)\]\]", r'<strong class="off">\1</strong>', t)
    return t

def plain(t):
    return re.sub(r"\*\*|\[\[|\]\]", "", str(t or "")).strip()

def ok(v):
    return v not in ("", None, "未確認")

def host_of(s):
    if s.get("cat") == "露營": return "營區"
    if s.get("cat") == "飯店旅館":
        return "飯店" if re.search(r"飯店|酒店", (s.get("kind") or "") + s.get("name", "")) else "旅店"
    return "民宿"

def type_of(s):
    k = s.get("kind") or ""
    if k and "（" not in k: return k
    return {"飯店旅館": "旅店"}.get(s.get("cat"), s.get("cat") or k)

def js(v):
    return json.dumps(v, ensure_ascii=False)

def post_entry(pid, s, old_tags):
    p = {"id": pid}
    if s.get("status") != "已上線": p["draft"] = True
    p.update(real=True, region=s.get("region", ""), area=s.get("area", ""), cat=s.get("cat", ""), type=type_of(s))
    if s.get("kind"): p["kind"] = s["kind"]
    p["title"] = plain(s.get("title"))
    p["excerpt"] = plain(s.get("excerpt"))
    p["tags"] = old_tags or [x for x in [s.get("region"), s.get("area"), s.get("cat")] if x]
    p["textCover"] = s.get("cover") or ["#F2C230", "#C98A1A", "#4A3410"]
    p["motif"] = s.get("motif") or "mount"
    p["host"] = host_of(s)
    if s.get("photo") in ("缺照片", "等商家授權"): p["soon"] = True
    for k in ("code", "lineUrl", "lineId", "video", "gRating", "gCount", "gDate", "mapUrl", "website", "breakfast"):
        if ok(s.get(k)): p[k] = str(s[k]).strip()
    for k in ("codeNote", "price", "roomsIntro", "spaces", "facilityText", "kitchen", "breakfastText", "dinner", "nearbyIntro", "priceBtn"):
        if ok(s.get(k)): p[k] = md(s[k])
    if ok(s.get("codeCond")): p["codeCond"] = md(s["codeCond"]).rstrip("。")
    for k in ("address", "capacity", "checkin"):
        if ok(s.get(k)): p[k] = html.escape(s[k].strip(), quote=False)
    pk = "，".join(x for x in [s.get("parking"), s.get("parkingNote")] if ok(x))
    if pk: p["parkingText"] = md(pk)
    bf = "，".join(x for x in [s.get("breakfast"), s.get("breakfastNote")] if ok(x))
    if bf: p["breakfastInfo"] = md(bf)
    if s.get("breakfastVeg"): p["breakfastVeg"] = True
    if s.get("dinnerVeg"): p["dinnerVeg"] = True
    p["intro"] = [md(t) for t in s.get("intro", []) if plain(t)]
    for k in ("indoor", "outdoor"):
        l = [md(t) for t in s.get(k, []) if plain(t)]
        if l: p[k] = l
    rows = [{k: md(r.get(k, "")) for k in ("floor", "type", "fit")} for r in s.get("roomRows", []) if any(plain(r.get(k)) for k in ("floor", "type", "fit"))]
    if rows: p["roomRows"] = rows
    rules = [{"cat": r.get("cat") or "其他", "text": md(r["text"])} for r in s.get("rules", []) if plain(r.get("text"))]
    if rules: p["rules"] = rules
    nb = [{k: (str(n.get(k) or "").strip()) for k in ("name", "group", "drive", "dist", "url")} for n in s.get("nearby", []) if plain(n.get("name"))]
    for n in nb: n["name"] = html.escape(n["name"], quote=False)
    if nb: p["nearby"] = nb
    render = HANDMADE.get(pid, "renderSimple")
    body = ", ".join(f"{k}:{js(v)}" for k, v in p.items())
    return f"  {{ {body}, render:{render} }},"

def default_ask(s):
    t = f"您好，我是從「Mika今晚住這裡」看到{s['name'].strip()}的資訊！\n\n想詢問＿＿月＿＿日\n＿＿位大人、＿＿位小孩，是否還有空房？"
    return t + (f"\n\n也想請問使用優惠碼 {s['code'].strip()} 的價格，謝謝！" if ok(s.get("code")) else "\n\n謝謝！")

def replace_block(src, name, body):
    pat = re.compile(rf"(/\* <後台產生：{name}> \*/\n)(.*?)(\s*/\* </後台產生：{name}> \*/)", re.S)
    if not pat.search(src): sys.exit(f"找不到區塊：{name}")
    return pat.sub(lambda m: m.group(1) + body + m.group(3), src)

def main(path):
    docs = json.load(open(path, encoding="utf-8"))
    stays = [(d["data"].get("slug") or d["id"], d["data"]) for d in docs if plain(d["data"].get("name"))]
    stays.sort(key=lambda x: -(x[1].get("order") or 0))
    src = SRC.read_text(encoding="utf-8")
    old_tags = {m.group(1): json.loads(m.group(2)) for m in re.finditer(r'\{ id:"([^"]+)".*?tags:(\[[^\]]*\])', src)}
    posts, deals, copies = [], [], []
    for pid, s in stays:
        if pid in HANDMADE:   # 手工版：保留原本那一筆，只更新優惠與文案
            pass
        else:
            posts.append(post_entry(pid, s, old_tags.get(pid)))
        if ok(s.get("code")) and s.get("deal") != "已結束":
            note = plain(s.get("codeNote")).replace("輸入折扣碼享 ", "").replace("輸入折扣碼享", "")
            line = f"專屬折扣碼 {s['code'].strip()}" + (f" · {note}" if note else "")
            deals.append(f'  {{ post:{js(pid)}, type:"折扣碼", start:0, end:Infinity, code:{js(s["code"].strip())}, line:{js(line)} }},')
        if ok(s.get("lineUrl")):
            copies.append(f'  {js(pid + "-ask")}: {js(s.get("askText") or default_ask(s))},')
        if ok(s.get("shareText")):
            copies.append(f'  {js(pid + "-share")}: {js(s["shareText"])},')
    src = replace_block(src, "文章", "\n".join(posts))
    src = replace_block(src, "優惠", "\n".join(deals))
    src = replace_block(src, "文案", "\n".join(copies))
    SRC.write_text(src, encoding="utf-8")
    print(f"文章 {len(posts)} 篇（另有手工版 {len([p for p,_ in stays if p in HANDMADE])} 篇）、優惠 {len(deals)} 筆、文案 {len(copies)} 段")

if __name__ == "__main__":
    main(sys.argv[1])

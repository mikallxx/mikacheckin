"""產生每間住宿的「揪團卡」圖片。

輸出到 source/img/<id>/：
  share-card.jpg  1080x1350 直式，給讀者存圖／傳到 LINE 群組
  og-card.jpg     1200x630 橫式，貼網址到 LINE / FB 時自動顯示的預覽圖

新增住宿：在 CARDS 加一筆，再執行 python3 source/make_cards.py
"""
import os, subprocess, json, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CARDS = [
    {
        "id": "hangwang",
        "photo": "01.jpg",
        "place": "宜蘭冬山｜包棟民宿",
        "name": "巷往 Villa",
        "stats": [("可住人數", "8～22 人"), ("房間", "6 間，都有衛浴")],
        "tags": ["一樓孝親房", "二樓檜木房", "KTV、麻將", "戲水池", "附早餐"],
        "deal": "優惠碼 MIKA888　包棟定價 75 折",
        "deal_note": "暑假、週六、連假及春節不適用",
        "url": "mikacheckin.com/hangwang",
    },
]

FONT = '"Noto Sans CJK TC","Noto Sans TC",sans-serif'
BASE_CSS = f"""
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:{FONT};color:#171717;background:#fff}}
.pill{{display:inline-block;border-radius:999px;font-weight:700}}
.tag{{background:#FCEDED;color:#A81919;font-weight:500}}
.stat{{background:#EFF4FF;border-radius:20px}}
.stat small{{display:block;color:#274B9B;font-weight:500}}
.stat b{{display:block;color:#274B9B;font-weight:900}}
.deal{{background:#FCEDED;color:#A81919;border-radius:20px;font-weight:700}}
.deal small{{display:block;font-weight:400;color:#A81919;opacity:.85}}
.foot{{display:flex;align-items:center;justify-content:space-between;border-top:2px solid #ececec}}
.brand b{{display:block;font-weight:900;color:#171717}}
.brand span{{color:#8a8a8e}}
.go{{background:#274B9B;color:#fff;font-weight:700;border-radius:999px}}
"""


def esc(s):
    return html.escape(s)


def portrait(c, photo):
    tags = "".join(f'<span class="pill tag" style="font-size:30px;padding:10px 26px">{esc(t)}</span>' for t in c["tags"])
    stats = "".join(f'<div class="stat" style="padding:22px 28px"><small style="font-size:26px">{esc(k)}</small><b style="font-size:42px;margin-top:4px">{esc(v)}</b></div>' for k, v in c["stats"])
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{BASE_CSS}
body{{width:1080px;height:1350px;overflow:hidden}}</style></head><body>
<div style="position:relative;height:560px;background:url('{photo}') center/cover">
  <span class="pill" style="position:absolute;top:40px;left:44px;background:#fff;color:#274B9B;font-size:30px;padding:12px 30px">揪團邀請</span>
</div>
<div style="padding:36px 56px 0">
  <div style="font-size:30px;color:#5f5e5a">{esc(c['place'])}</div>
  <div style="font-size:76px;font-weight:900;letter-spacing:-1px;margin:2px 0 24px">{esc(c['name'])}</div>
  <div style="display:grid;grid-template-columns:1fr 1.3fr;gap:18px">{stats}</div>
  <div style="display:flex;flex-wrap:wrap;gap:14px;margin-top:22px">{tags}</div>
  <div class="deal" style="margin-top:22px;padding:18px 28px;font-size:32px">{esc(c['deal'])}<small style="font-size:24px;margin-top:4px">※{esc(c['deal_note'])}</small></div>
</div>
<div class="foot" style="position:absolute;left:56px;right:56px;bottom:40px;padding-top:28px">
  <div class="brand"><b style="font-size:34px">今晚住這裡 Mika Check-in</b><span style="font-size:26px">房間照片和完整介紹：{esc(c['url'])}</span></div>
</div>
</body></html>"""


def landscape(c, photo):
    tags = "".join(f'<span class="pill tag" style="font-size:22px;padding:7px 18px">{esc(t)}</span>' for t in c["tags"][:4])
    stats = "".join(f'<div class="stat" style="padding:14px 18px;border-radius:14px"><small style="font-size:18px">{esc(k)}</small><b style="font-size:28px;margin-top:2px">{esc(v)}</b></div>' for k, v in c["stats"])
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{BASE_CSS}
body{{width:1200px;height:630px;overflow:hidden;display:flex}}</style></head><body>
<div style="position:relative;width:560px;height:630px;background:url('{photo}') center/cover">
  <span class="pill" style="position:absolute;top:28px;left:28px;background:#fff;color:#274B9B;font-size:22px;padding:8px 22px">揪團邀請</span>
</div>
<div style="flex:1;padding:40px 44px;display:flex;flex-direction:column">
  <div style="font-size:22px;color:#5f5e5a">{esc(c['place'])}</div>
  <div style="font-size:56px;font-weight:900;letter-spacing:-1px;margin:2px 0 20px">{esc(c['name'])}</div>
  <div style="display:grid;grid-template-columns:1fr 1.35fr;gap:12px">{stats}</div>
  <div style="display:flex;flex-wrap:wrap;gap:10px;margin-top:18px">{tags}</div>
  <div class="deal" style="margin-top:18px;padding:12px 18px;border-radius:14px;font-size:22px">{esc(c['deal'])}</div>
  <div class="brand" style="margin-top:auto"><b style="font-size:22px">今晚住這裡 Mika Check-in</b><span style="font-size:18px">{esc(c['url'])}</span></div>
</div>
</body></html>"""


def main():
    jobs = []
    tmp = os.path.join(ROOT, "source", ".cards_tmp")
    os.makedirs(tmp, exist_ok=True)
    for c in CARDS:
        photo = "file://" + os.path.join(ROOT, "source", "img", c["id"], c["photo"])
        out_dir = os.path.join(ROOT, "source", "img", c["id"])
        for kind, fn, w, h in [("share", portrait, 1080, 1350), ("og", landscape, 1200, 630)]:
            page = os.path.join(tmp, f"{c['id']}-{kind}.html")
            open(page, "w", encoding="utf-8").write(fn(c, photo))
            jobs.append({"page": "file://" + page, "out": os.path.join(out_dir, f"{kind}-card.jpg"), "w": w, "h": h})
    subprocess.run(["node", "-e", f"""
const {{chromium}}=require('playwright');
(async()=>{{const b=await chromium.launch();
for(const j of {json.dumps(jobs)}){{const p=await b.newPage({{viewport:{{width:j.w,height:j.h}}}});
 await p.goto(j.page);await p.waitForTimeout(300);
 await p.screenshot({{path:j.out,type:'jpeg',quality:88}});await p.close();console.log('card',j.out);}}
await b.close();}})();"""], check=True)
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)


if __name__ == "__main__":
    main()

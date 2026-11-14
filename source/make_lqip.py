"""Generate tiny blurred placeholders (LQIP) for every photo in source/img.

Writes them into source/index.html between /*LQIP-START*/ and /*LQIP-END*/
as a JS object keyed by image path without the "_s" suffix, e.g.
  "img/hangwang/01.jpg": "data:image/jpeg;base64,..."
Run automatically by build_site.py, so new photos get a placeholder too.
"""
import base64, io, json, os, re
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(ROOT, "img")
INDEX = os.path.join(ROOT, "index.html")


def lqip(path):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    tw = 32
    im = im.resize((tw, max(1, round(h * tw / w))), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=55, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def main():
    data = {}
    for folder in sorted(os.listdir(IMG_DIR)):
        d = os.path.join(IMG_DIR, folder)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")) or "_s." in f or "-card." in f:
                continue
            data[f"img/{folder}/{f}"] = lqip(os.path.join(d, f))
    s = open(INDEX, encoding="utf-8").read()
    block = "/*LQIP-START*/const LQIP=" + json.dumps(data, separators=(",", ":")) + ";/*LQIP-END*/"
    s, n = re.subn(r"/\*LQIP-START\*/.*?/\*LQIP-END\*/", lambda m: block, s, flags=re.S)
    if n != 1:
        raise SystemExit("LQIP markers not found in index.html")
    open(INDEX, "w", encoding="utf-8").write(s)
    print(f"LQIP: {len(data)} images, {len(block)//1024} KB")


if __name__ == "__main__":
    main()

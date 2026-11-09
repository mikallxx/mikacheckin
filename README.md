# Mika Check-in｜今晚住這裡

Mika 的住宿開箱攻略網站：https://mikacheckin.com

## 資料夾說明

- `dist/`：正式網站的檔案，Cloudflare Pages 發布的就是這個資料夾（不要手動修改，會被重新產生）
- `source/index.html`：網站內容與版型的原始檔（文章、優惠、配色都在這裡）
- `source/img/`：網站用的照片，每間住宿一個資料夾（例如 `hangwang/`）
- `source/build_site.py`：把原始檔產生成正式網站的程式

## 更新網站

1. 修改 `source/` 裡的內容
2. 執行 `python3 source/build_site.py`（需要 Node.js 與 Playwright，用來預先產生文章頁）
3. 把變更推送到 GitHub，Cloudflare Pages 會自動重新發布

## Cloudflare Pages 設定

- Framework preset：None
- Build command：留空
- Build output directory：`dist`

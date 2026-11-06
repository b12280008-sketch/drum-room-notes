# 鼓房筆記

這是爵士鼓練習筆記。每頁有建議 BPM、一小節 4/4 節奏譜、試聽、練習步驟和容易打錯的地方。

## 開發與預覽

需要 Python 3 和瀏覽器。在專案根目錄執行以下指令。

```sh
python3 scripts/build.py
python3 scripts/build.py --check
python3 -m http.server 8000 --directory docs
```

在瀏覽器開啟 `http://localhost:8000/`。網站由 `docs/` 的靜態檔案組成，頁面的合成節奏在瀏覽器內播放。

## 新增一張卡片

照 [AGENTS.md](AGENTS.md) 的格式，在 `content/` 新增一個 JSON。建置程式會檢查欄位及節奏格數，按照 `order` 產生首頁清單、卡片頁和下一張連結。建置後執行 `--check`，確認實際網站與來源資料相符。

## 擴充示範

初版有「8 Beat 基本節奏」與「反拍大鼓」兩張卡片。接著依 `AGENTS.md` 的任務範例，加入 [第 4 拍過門的資料](content/fourth-beat-fill.json) 並重建網站。

- 新增 `docs/practice/fourth-beat-fill/index.html`，首頁自動列出第三張卡片。
- 「反拍大鼓」的下一張連結自動指向新頁面。新增卡片的提交只包含一個來源資料檔與對應的網站輸出。
- 執行建置檢查並核對四頁的相對連結。從首頁開啟新卡片，用鍵盤啟動與停止 64 BPM 的示範，確認節奏譜的高亮會跟著更新。
- 在 375 px 的預覽中確認整頁寬度符合視窗，節奏譜仍可水平捲動。

## GitHub Pages

Repository 的 Settings → Pages 選擇 Deploy from a branch。使用 `main` 分支和 `/docs` 資料夾。建置結果與來源一併提交，助教可從 Repository 檢查規則，也可以直接瀏覽網站。

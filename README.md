# PTT Crawler

用於爬取 PTT 特定看板特定標題文章，並透過 LINE Bot 發送文章訊息

## 安裝與設定

### 前置需求

- Python 3.7 或以上版本
- 有效的 LINE Token
- LINE 使用者 ID

### 安裝相依套件

```bash
pip install -r requirements.txt
```

### 環境變數設定

編輯 `.env.example` 檔案，填入 LINE Token 和 使用者 ID，並將檔案重新命名為 `.env`：

```
LINE_TOKEN=your_line_token_here
LINE_USER_ID=your_line_user_id_here
```

## 使用方式

執行主程式：

```bash
python ptt_crawler.py
```

### 功能說明

- 爬取指定 PTT 看板的最新文章
- 根據票種、藝人關鍵字篩選文章標題
- 記錄已爬取文章，避免重複
- 透過 LINE Bot 即時推送通知

## 自訂設定

在 `ptt_crawler.py` 的 `main()` 中修改以下參數：

- `board`：目標看板名稱
- `ticket_keywords`：票種關鍵字
- `artist_keywords`：藝人關鍵字
- `max_pages`：爬取最大頁數
- 通知訊息格式
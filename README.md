# PTT Crawler

用於爬取 PTT 特定看板特定文章並透過 LINE Bot 發送通知

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
- 根據關鍵字過濾文章
- 將符合條件的文章資訊透過 LINE 發送通知

## 自訂設定

您可以在程式碼中修改以下參數：

- 目標看板名稱
- 爬取頁數
- 篩選關鍵字
- 通知訊息格式

## 授權條款

MIT License
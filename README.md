# 監控系統（含 SQL 注入漏洞教學版）

這是一個「系統監控平台」，首頁為登入頁面（帳號／密碼欄位）。
**刻意**在帳號欄位拼接 SQL 語法，存在典型的 SQL 注入漏洞，供資安課程教學與示範攻擊使用。

## 功能

- 登入頁面：帳號 + 密碼（帳號欄存在 SQL 注入漏洞）
- 登入成功後進入監控儀表板
- 儀表板顯示 CPU、記憶體、磁碟、網路流量等即時系統資源
- 記錄所有登入嘗試（成功／失敗）並顯示最近記錄
- Debug 模式：登入失敗時顯示實際執行的 SQL 語句，方便觀察注入點

## 開始使用

```bash
# 建立虛擬環境並安裝依賴
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 啟動服務（首次啟動會自動建立資料庫與示範帳號）
.venv/bin/python app.py
# 預設使用 5000 埠；若被佔用（macOS AirPlay 常佔用 5000），改用：
PORT=5008 .venv/bin/python app.py
```

開啟瀏覽器前往 http://localhost:5000（或對應埠號）

## 示範帳號

| 帳號 | 密碼        | 角色  |
|------|-------------|-------|
| admin | password123 | admin |
| alice | alice123    | user  |
| bob   | bob123      | user  |

## SQL 注入漏洞說明

「帳號」欄位直接以字串拼接方式放入 SQL 查詢：

```python
query = "SELECT * FROM users WHERE username = '{}' AND password = '{}'".format(
    username, password
)
```

正常登入時執行的查詢：

```sql
SELECT * FROM users WHERE username = 'admin' AND password = 'password123'
```

### 攻擊示範

在帳號欄位輸入 `' OR '1'='1' -- `（閉合字串、注入恆真條件並註解掉後半段），即可繞過帳號驗證：

```text
帳號欄：' OR '1'='1' --
密碼欄：任意
```

```sql
SELECT * FROM users WHERE username = '' OR '1'='1' --' AND password = '...'
```

會回傳所有使用者，並以第一筆（admin）的身分登入。

更進一步，想把自己變成 admin（`--` 是 SQL 註解，吃光後面的條件）：

```text
帳號欄：admin' --
密碼欄：任意
```

```sql
SELECT * FROM users WHERE username = 'admin' --' AND password = '任意'
```

- `'` 閉合原本的字串
- `--` 把後面的 `AND password = ...` 整段註解掉
- 結果：直接以 admin 身分登入，取得最高權限

## 修補方式（正式版應這樣做）

使用參數化查詢，讓使用者輸入永遠只是「資料」而非「程式碼」：

```python
cur = conn.execute(
    "SELECT * FROM users WHERE username = ? AND password = ?",
    (username, password),
)
```

密碼也不該以明文儲存，應使用 bcrypt / argon2 等演算法加鹽雜湊。

## 檔案結構

```
ais3/
├── app.py                # Flask 主程式（含漏洞登入邏輯）
├── requirements.txt
├── monitoring.db         # SQLite 資料庫（首次啟動自動建立）
├── templates/
│   ├── login.html        # 登入頁面
│   └── dashboard.html    # 監控儀表板
└── README.md
```
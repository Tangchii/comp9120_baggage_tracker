# 組員安裝說明（Mac，本機版）

照順序做，大約 10 分鐘。只有第一次要裝東西，之後每次開只要第 6 步。

## 0. 先解壓

把 `prototype_for_teammates.zip` 解壓，把裡面的 `prototype` 資料夾放到桌面。
（路徑盡量簡單，不要放有中文或空白太多的路徑。）

## 1. 裝 PostgreSQL（只需要第一次）

1. 到 https://postgresapp.com 下載 Postgres.app，裝好後打開它，按 Start，
   等它顯示正在運行（running）。
2. 不用自己建任何東西，下一步用指令建。

## 2. 打開終端機，進到資料夾

打開「終端機」（Terminal），輸入 `cd ` 後面加一個空白，
把桌面的 `prototype` 資料夾直接拖進終端機視窗，再按 Enter。
（這樣路徑會自己填好，不用手打。）

## 3. 建資料庫、匯入資料（只需要第一次）

在終端機依序貼上，每行按一次 Enter：

```bash
PG=/Applications/Postgres.app/Contents/Versions/latest/bin
$PG/createdb baggage_demo
$PG/psql -d baggage_demo -f database/01_schema.sql
$PG/psql -d baggage_demo -f database/02_sample_data.sql
```

- `01` 是建資料表，`02` 是匯入示範資料，順序不能反。
- 如果 `createdb` 說資料庫已存在，沒關係，跳過那行即可；
  但匯入前要用乾淨的庫，見最下面的「資料亂掉怎麼重置」。

## 4. 裝 Python 套件（只需要第一次）

```bash
python3 -m venv ~/.venvs/comp9120-baggage
~/.venvs/comp9120-baggage/bin/pip install -r requirements.txt
```

## 5. 啟動程式

```bash
~/.venvs/comp9120-baggage/bin/streamlit run app.py
```

瀏覽器打開 http://localhost:8501 （通常會自動開）。
要關掉：回到終端機按 `Control + C`。

## 6. 之後每次要開（最簡單）

1. 先打開 Postgres.app（確認它在運行）。
2. 雙擊資料夾裡的 `Open-Local.command`。
3. 瀏覽器會自己打開 http://localhost:8501 。

（雙擊若被 Mac 擋下來：右鍵點它 →「打開」→ 再按「打開」。）

## 登入帳號（示範用）

| 角色 | 登入方式 |
|---|---|
| 旅客 | 行李標籤 `100006`，Email `txz9120.eva.liu.05@gmail.com`（登入頁也有一鍵填入按鈕） |
| 地勤 | 密碼 `staff9120` |
| 主管 | 角色選 Supervisor，密碼 `super9120` |

## 常見問題

- **Cannot connect to PostgreSQL**：Postgres.app 沒開，或第 3 步沒做完。
  先開 Postgres.app 再重新啟動程式。
- **02_sample_data 說資料表不是空的**：代表這個庫之前匯過資料。
  依序跑這三行重置（會清掉舊的示範資料）：

  ```bash
  $PG/psql -d baggage_demo -f database/reset_database.sql
  $PG/psql -d baggage_demo -f database/01_schema.sql
  $PG/psql -d baggage_demo -f database/02_sample_data.sql
  ```

  展示/錄影前想回到最初狀態，也是跑這三行。
- **8501 被占用 / 開出舊畫面**：舊的程式還在跑。回舊終端機按 `Control + C`，
  或改用 `streamlit run app.py --server.port 8502` 再開 http://localhost:8502 。
- **Windows 電腦**：步驟一樣，但要自己裝 PostgreSQL（官網 EDB 安裝版）和
  Python，指令裡的路徑會不同。嫌麻煩的話等雲端版網址，直接開連結就好，
  不用裝任何東西。

## 注意

- 每個人電腦上的資料庫是各自獨立的，你在自己電腦確認裝載，
  隊友的電腦不會跟著變。要共用同一份資料，用雲端版（Neon）。
- 改程式前先講好誰在改，不要兩個人同時改同一個檔案。

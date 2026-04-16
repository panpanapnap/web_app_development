# 路由設計文件：活動報名系統

本文件基於 PRD、系統架構與資料庫設計，詳細規劃 Flask 的所有路由介面與前後端資料的對應藍圖。為保持架構乾淨，路由主要區分為 `events` 與 `registrations` 兩個 Blueprint 模組。

## 1. 路由總覽表格

| 模組 | 功能 | HTTP 方法 | URL 路徑 | 對應模板 | 說明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Events** | 首頁 / 活動列表 | `GET` | `/` | `templates/events/index.html` | 顯示所有開放與未截止的活動 |
| **Events** | 建立活動頁面 | `GET` | `/events/create` | `templates/events/create.html` | 主辦方建立活動的 HTML 表單 |
| **Events** | 建立活動 | `POST` | `/events/create` | — | 接收並驗證表單，寫入資料庫後重導 |
| **Events** | 活動詳細資訊 | `GET` | `/events/<id>` | `templates/events/detail.html` | 單一活動詳細圖文，以及進入報名按鈕 |
| **Events** | 編輯活動頁面 | `GET` | `/events/<id>/edit` | `templates/events/edit.html` | 編輯指定活動用的資料載入表單 |
| **Events** | 更新活動 | `POST` | `/events/<id>/update` | — | 寫入新的編輯內容，成功後重導 |
| **Events** | 刪除活動 | `POST` | `/events/<id>/delete` | — | 刪除該活動與所有關聯報名者，重導 |
| **Regs** | 活動名單管理 | `GET` | `/events/<id>/registrations` | `templates/registrations/manage.html`| 主辦方用來檢視與管理報名狀態名單 |
| **Regs** | 線上報名頁面 | `GET` | `/events/<id>/register` | `templates/registrations/new.html` | 學生填寫學號等個資表單 |
| **Regs** | 送出線上報名 | `POST` | `/events/<id>/register` | — | 利用資料庫 Transaction 排隊防超賣機制 |
| **Regs** | 我的報名總覽 | `GET` | `/my/registrations` | `templates/registrations/my_list.html`| 學生檢視自己所有報名(成功或候補)紀錄 |
| **Regs** | 修改聯絡資料 | `POST` | `/registrations/<id>/update` | — | 修改自己送出過的報名電話等資訊 |
| **Regs** | 取消報名 | `POST` | `/registrations/<id>/cancel` | — | 放棄資格並觸動下一順位候補轉正功能 |

*(備註：因傳統 HTML Form 不支援 PUT 或 DELETE 請求，編輯更新與刪除路由皆採用 `POST` 來實現 RESTful 概念。)*

---

## 2. 每個路由的詳細說明

### 2.1 Events 模組 (`app.routes.events`)

#### `GET /` (首頁)
- **輸入**：無。
- **處理邏輯**：呼叫 `EventModel.get_all()` 回傳最新活動資料。
- **輸出**：渲染 `events/index.html`，以卡片形式呈現。
- **錯誤處理**：資料庫無資料時，畫面顯示「目前暫無開放的活動」。

#### `GET /events/create`
- **輸入**：無。
- **輸出**：渲染空白或帶有預設值的 `events/create.html` 頁面。

#### `POST /events/create`
- **輸入**：接收表單數值：`title`、`capacity`、`deadline`、`description`、`location`。
- **處理邏輯**：驗證名稱不能為空、限制人數只能填入正整數，驗證通過呼叫 `EventModel.create()`。
- **輸出**：使用 `flash` 提供成功通知，並 `redirect` 回首頁。
- **錯誤處理**：格式錯誤時，回傳該頁面並附上 HTML Alert 訊息阻擋。

#### `GET /events/<id>`
- **輸入**：URL 夾帶的活動識別碼 `event_id`。
- **處理邏輯**：透過 `EventModel.get_by_id(id)` 撈取該活動。
- **輸出**：渲染至 `events/detail.html`。
- **錯誤處理**：ID 找不到時回傳 `abort(404)`。

#### `POST /events/<id>/update`
- **輸入**：修改後的欄位，伴隨隱藏的 `<id>` 資訊。
- **處理邏輯**：呼叫 `EventModel.update()`。
- **輸出**：重新導向回修改後的 `/events/<id>`。

#### `POST /events/<id>/delete`
- **輸入**：特定的活動 ID。
- **處理邏輯**：觸發 `EventModel.delete()` 移除自己及附屬名單（CASCADE 機制）。
- **輸出**：重定向 `/` 網站起點。

### 2.2 Registrations 模組 (`app.routes.registrations`)

#### `GET /events/<id>/registrations`
- **輸入**：活動 `<id>`。
- **處理邏輯**：依序呼叫 `EventModel.get_by_id()` 和 `RegistrationModel.get_by_event()` 彙整出總名單與目前剩餘座位。
- **輸出**：渲染給主辦方專用的 `registrations/manage.html` 清單資料。

#### `GET /events/<id>/register`
- **輸入**：活動 `<id>`。
- **處理邏輯**：首看該事件過期了沒，若未過期則繼續。
- **輸出**：呈現 `registrations/new.html` 請學生輸入自己的逢甲學號。
- **錯誤處理**：要是已過期，立刻攔阻不給進入並給予提示。

#### `POST /events/<id>/register`
- **輸入**：`student_id`, `name`, `phone` 以及路由的 `event_id`。
- **處理邏輯**：這段是**MVP 核心**，使用 Transactional 的 `RegistrationModel.register()` 把排隊卡位的工作交給資料表鎖。返回最終判斷。
- **輸出**：可能是「您已報名成功」或者「目前已滿進入候補」，重導到學生檢視頁面。

#### `GET /my/registrations`
- **輸入**：Session 或 URL Query 中獲得的 `student_id`。
- **處理邏輯**：提取專屬該學號的歷史足跡 `RegistrationModel.get_by_student()`。
- **輸出**：將資料餵給 `registrations/my_list.html`。

#### `POST /registrations/<id>/cancel`
- **輸入**：一筆已經存在的報名 ID。
- **處理邏輯**：呼叫 `cancel()`，系統狀態轉換，系統底層再抓取下一位幸運兒修改替補成功。
- **輸出**：狀態閃燈通知「已經取消」，頁面重載保持在目前列表上。

---

## 3. Jinja2 模板清單

將所有 HTML 清單切割為具有統一風格的範本擴充：

- `templates/base.html`：基底母版，用以包含統一的 Header 導覽列與 Bootstrap (或 Tailwind) CSS 設定檔匯入。
- `templates/events/index.html` (繼承自 base)：首頁列表呈現區。
- `templates/events/create.html` (繼承自 base)：寫入活動資料表的大型表單。
- `templates/events/edit.html` (繼承自 base)：預填完資料的修改活動大表。
- `templates/events/detail.html` (繼承自 base)：顯示大型橫幅、解說與一鍵跳轉的細節頁。
- `templates/registrations/manage.html` (繼承自 base)：採用 `<table/>` 表格，為社團主辦方印出清單。
- `templates/registrations/new.html` (繼承自 base)：單調、好操作的報名資料填寫表格，支援手機版 (RWD)。
- `templates/registrations/my_list.html` (繼承自 base)：羅列逢甲學生的歷屆戰績及標籤。

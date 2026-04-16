# 流程圖設計文件：活動報名系統

本文件基於 `docs/PRD.md` 與 `docs/ARCHITECTURE.md`，視覺化呈現系統的使用者操作路徑、系統資料交換流程，以及相關功能的對照表。

## 1. 使用者流程圖（User Flow）

此流程圖描述「逢甲學生（參與者）」與「活動主辦方」在進入系統後，各自可以進行的操作路徑與流程決策。

```mermaid
flowchart LR
    Start([進入系統首頁]) --> Role{身分與目的？}
    
    %% 學生的操作路徑
    Role -->|逢甲學生| Home_Student[瀏覽活動列表]
    Home_Student --> Action_Student{選擇操作}
    
    Action_Student -->|看活動| Event_Detail[查看活動詳細資訊]
    Event_Detail --> Register[填寫報名表單]
    Register --> Submit_Reg{送出報名}
    Submit_Reg -->|尚有名額| Reg_Success([報名成功])
    Submit_Reg -->|名額已滿| Reg_Waitlist([排入候補])
    
    Action_Student -->|管理己報名| My_Regs[我的報名紀錄]
    My_Regs --> Edit_Reg[修改報名資料]
    My_Regs --> Cancel_Reg([取消報名])
    Cancel_Reg -.->|系統自動| Notify_Waitlist[通知候補人員遞補]
    
    %% 主辦方的操作路徑
    Role -->|活動主辦方| Home_Organizer[主辦方控制台]
    Home_Organizer --> Action_Org{選擇操作}
    
    Action_Org -->|建立新活動| Create_Event[填寫活動與限制名額]
    Create_Event --> Publish_Event([發布活動])
    
    Action_Org -->|管理現有活動| Manage_Events[選擇特定活動]
    Manage_Events --> View_List[查看報名與候補名單]
    View_List --> Export_List([匯出名單])

    classDef student fill:#d4edda,stroke:#28a745
    classDef organizer fill:#cce5ff,stroke:#007bff
    classDef terminal fill:#f8d7da,stroke:#dc3545
    
    class Home_Student,Event_Detail,Register,My_Regs,Edit_Reg student
    class Reg_Success,Reg_Waitlist,Cancel_Reg terminal
    class Home_Organizer,Create_Event,Manage_Events,View_List organizer
    class Publish_Event,Export_List terminal
```

## 2. 系統序列圖（Sequence Diagram）

此序列圖詳細描繪了最核心也是問題最多的操作：**「使用者看中活動並送出報名表單」**，這中間系統各元件如何互動，包含防止超賣與自動候補的資料庫交易檢查流程。

```mermaid
sequenceDiagram
    actor User as 逢甲學生
    participant Browser as 瀏覽器
    participant Route as Flask Route (Controller)
    participant Model as Database Model
    participant DB as SQLite

    User->>Browser: 1. 填寫報名資料並點擊「送出」
    Browser->>Route: 2. POST /events/{id}/register (傳遞表單資料)
    
    Route->>Model: 3. 呼叫邏輯 `process_registration(data)`
    
    %% 資料庫 Transaction 區塊
    rect rgb(240, 248, 255)
        Note over Model, DB: 啟動 SQLite Transaction (防止超賣並鎖保護)
        Model->>DB: 4. SELECT count(*) 查詢已報名人數
        DB-->>Model: 5. 回傳目前人數
        
        alt 人數 < 活動上限
            Model->>DB: 6a. INSERT INTO registrations (status='成功')
            DB-->>Model: 7a. 存檔完成
        else 人數 >= 活動上限
            Model->>DB: 6b. INSERT INTO registrations (status='候補')
            DB-->>Model: 7b. 存檔完成
        end
    end
    
    Model-->>Route: 8. 回傳資料庫報名結果 (Success 或 Waitlisted)
    
    alt 報名成功
        Route-->>Browser: 9a. 重導向至「詳細資料」並顯示「報名成功」
    else 列入候補
        Route-->>Browser: 9b. 重導向至「詳細資料」並顯示「已排入候補」
    end
```

## 3. 功能清單對照表

將上述流程對應到實際的 Flask 路由規劃中。

| 主要功能 | 說明 | URL 路徑 (Route) | HTTP 方法 (Method) |
| :--- | :--- | :--- | :--- |
| **首頁/活動列表** | 顯示目前所有可報名的活動清單 | `/` 或 `/events` | `GET` |
| **活動詳細資訊** | 顯示單一活動內容介紹、報名時間與剩餘名額 | `/events/<id>` | `GET` |
| **線上報名 (表單)** | 顯示該活動的報名填寫頁面 | `/events/<id>/register` | `GET` |
| **線上報名 (送出)** | 接收表單，進行名單邏輯處理（含候補判斷） | `/events/<id>/register` | `POST` |
| **建立新活動 (表單)**| 主辦方的建立新活動設定頁面 | `/events/create` | `GET` |
| **建立新活動 (送出)**| 接收新活動資料並存入資料庫 | `/events/create` | `POST` |
| **報名名單管理** | 主辦方查看該活動的報名、候補人員狀態 | `/events/<id>/registrations` | `GET` |
| **我的報名紀錄** | 學生總覽自己報名且有效或候補中的活動 | `/my/registrations` | `GET` |
| **修改報名資料** | 送出更新自己的聯絡資訊等 | `/registrations/<reg_id>/edit` | `POST` |
| **取消報名** | 放棄參與活動（後端會自動觸發另一位候補者遞補） | `/registrations/<reg_id>/cancel` | `POST` |

*(註：為簡潔，修改或取消動作皆使用 `POST` 搭配表單實現，以符合標準 HTML 無法直接送出 PUT/DELETE 的實作方式)*

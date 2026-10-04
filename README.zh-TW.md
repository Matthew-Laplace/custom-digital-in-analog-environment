# Virtuoso Standard-Cell Layout

[English](README.md) | [日本語](README.ja.md) | [繁體中文](README.zh-TW.md)

一套 agent skill，把 Cadence Virtuoso 上的標準元件或自訂數位區塊，從空的
artifact 集合帶到有憑據支撐的繞線完成狀態。

標準元件自動化幾乎都敗在同幾個地方：`physConfig` 還沒生效就先把 layout 建好；
cell 依錯誤的邊界圖形擺放；電源軌被當成理所當然已連通；完成率顯示 100% 就
當作繞線成功；雙孔要求被當成保證。這套 skill 就是繞著這些失敗點設計的。

```text
Stage order      artifact set -> placement -> M1 supply tracks -> route
                 feedback -> signal routing -> tap/DRC -> LVS interpretation

Evidence layers  command-completed -> connectivity-closed
                 -> detailed-geometry-closed -> via-contract-closed
                 -> saved-readback-closed
```

每一個箭頭都是關卡，不是形式。後面的階段不會補上前面缺的關卡，某一層通過也
不能代替另一層。

## 涵蓋範圍

- **Artifact 建立。** 把 layout 建立、`physConfig` 建立、來源產生、config 與
  connectivity 參照指派、active Binder 更新、cross-probe 驗證當成各自獨立的
  狀態轉換。Layout XL 啟動成功，不能證明後面任何一個狀態存在。
- **依真實邊界擺放。** 用 PR 邊界圖形，而不是 instance 或 master 的
  bounding box；合法 transform 集合要從 library 讀回，不能假設；受保護的
  group 以剛體方式平移。
- **擺放與等價 pin 的聯合搜尋。** 合法左右鏡像、三端點共享樹拓樸、線性
  鏈聚類，以及明確的固定端點，全部以整條 net 的成本評分，而不是成對距離。
- **佔用策略。** 預設單一高度；以去耦電容（decoupling capacitor）優先，
  求整數 site 的精確覆蓋；只有狹窄殘餘空隙才用合法 filler 收尾；多高度
  cell 必須逐次交易明確啟用。
- **電源軌。** 由繞線足跡決定尺寸的等長 M1 電源與接地軌；外側上下兩條軌
  必須是接地，並且與 cell rail 有實際接觸。
- **繞線驗收。** 上述有順序的證據向量，加上從資料庫讀回、而非採信 router
  自身摘要的嚴格 effective via 陣列關卡。
- **Tap cell 插入。** 依製程確認 latch-up 間距，換算成每列有限數量與邊緣
  區間，並在該次執行獲准時，用目標自身的 DRC 驗證。
- **寫入安全。** 單一寫者的 lease、有界的請求預算、批次化，以及面對含糊
  回傳時只做一次有界對帳，不盲目重試。

## 目錄結構

```
SKILL.md                               進入點、階段順序、關卡
README.md                              英文版
README.ja.md                           日文版
README.zh-TW.md                        本檔案
ATTRIBUTION.md                         來源與證據等級
LICENSE                                MIT
agents/openai.yaml                     skill 介面定義
references/
  bounded-operation-contract.md        所有權、lease、預算、證據
  geometry-execution.md                OA 編輯機制、binding、經驗法則
  wire-assistant-routing.md            Route API、via 與 push 語意
  local-layout-planning.md             離線規劃 helper
  skil-coding-patterns.md              SKILL 程式碼慣例
scripts/
  layout_plan.py                       純計算規劃 helper
  test_layout_plan.py                  對應測試
```

## 安裝為 Skill

把整個目錄複製到 agent 的 skill 資料夾，例如：

```bash
cp -R virtuoso-standard-cell-layout ~/.codex/skills/virtuoso-standard-cell-layout
```

內容是純 Markdown 加上兩個只用標準函式庫的 Python 檔案，不需要建置，也不
需要安裝相依套件。執行內附測試：

```bash
python3 scripts/test_layout_plan.py
```

## 誠實的界線

- 這套 skill **不執行** DRC、LVS、萃取或 signoff，也不附規則 deck。它的
  職責是準備候選結果，並解讀另一個獨立綁定的驗證流程、依當前製程規則產生
  的結果。
- 它**不附** live layout adapter。內附的 Python 是純計算，不碰資料庫、
  檔案系統或網路；真正連到工作階段的 callback 由你自己的專案提供。
- 這裡記錄的 Route API 名稱與語意，來自特定安裝世代的閱讀。廠商文件與
  已安裝符號會隨版本變動，使用前請在自己的版本上確認精確簽名。
- half-perimeter wire length 或 minimum spanning tree 這類幾何成本是**擺放
  代理指標**，不是實際金屬線長縮短的證據，不應單憑它主張繞線長度改善。
- 範例中出現的數值示範的是確認程序，不是可移植的預設值。製程規則、層名、
  合法 master 與合法方向，一律取自眼前的設計。

## 不可妥協的規則

1. **只有一個寫者。** 一個 live 工作階段的幾何寫者永遠只有一個。讀取者要
   等變更靜止；把控制權交回使用者之前，必須釋放 lease。
2. **不儲存不合格的候選。** 連接性、詳細幾何或嚴格 via 契約失敗的候選，
   一律保持明確的 live 未儲存狀態，並保留最後一次接受的磁碟狀態。
3. **不對含糊的變更重試。** 逾時或含糊回傳就是結果未知。只做一次有界對帳，
   不得先盲目重試、儲存或清理。
4. **保留受保護物件。** 文字、label、pin 圖形、既有繞線、電源幾何，以及
   terminal 對 net 的對應，除非該精確物件落在獲准的寫入集合內，否則一律
   受保護。
5. **要求不等於保證。** 向 router 要求雙孔 via、最大規則或 push，都不證明
   它們真的發生。要讀回資料庫，要求精確的契約。

## 適用範圍說明

這是一套實務工程 skill，不是規格書。有些規則描述的是針對特定工具世代確認過的
做法，也有幾處記錄了真實失敗得到的教訓。當一條規則取決於製程、library 或
站點慣例時，文中會明講；請不要把某個在地慣例普遍化成可移植規則。

## 授權

MIT，詳見 `LICENSE`。參考過的公開來源列在 `ATTRIBUTION.md`。本倉庫未再
散布任何第三方程式碼或廠商文件。

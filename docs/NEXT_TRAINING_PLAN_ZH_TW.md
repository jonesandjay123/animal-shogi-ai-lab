# 下一階段訓練計畫（繁體中文）

日期：2026-07-03

本文件是「訓練出更強的 AI、在介面上與人對弈」這個目標的下一步計畫與執行紀錄。閱讀順序上，本文件取代 `docs/NEXT_TRAINING_STEPS.md` 成為目前的行動依據（該文件的 Phase 9D 評估精神已部分落實在本次工作中）。

---

## 1. 現況盤點（2026-07-03，本機實測）

**重要發現：文件與本機實際狀態不一致。**

- `docs/HANDOFF.md` 與 `docs/NEXT_TRAINING_STEPS.md` 記載的 5M vs-heuristic baseline
  （`checkpoints/animal_shogi_maskable_ppo_vs_heuristic/.../final_model.zip`）**不存在於這台電腦上**。
  該次訓練應是在另一個環境完成的，checkpoint 沒有跟著 git 帶過來（`checkpoints/` 不進版控）。
- 本機實際擁有的模型只有一個：

```text
checkpoints/animal_shogi_maskable_ppo_vs_random/maskable_ppo_vs_random_black_20260525_140008/final_model.zip
（MaskablePPO，黑方視角，對手為 RandomAgent，5,000,000 步，2026-05-25 完成）
```

### 基準實測（本次新增的 heuristic 評估功能）

| 對手 | 局數 | 模型勝率 | 平均步數 |
|---|---|---|---|
| random | 100 | **100%** | 5.44 手 |
| heuristic（一層搜索） | 100 | **0%** | 8.00 手 |

結論非常清楚：**現有模型已把 random 完全打爆，但完全打不贏一層搜索的 HeuristicAgent。**
「更強的 AI」的第一個具體目標，就是把對 heuristic 的勝率從 0% 拉起來。

---

## 2. 下一步建議：對手池（Opponent Pool）訓練 + 熱啟動

### 為什麼是這個方案

1. **只跟 random 練已經沒有東西可學**（勝率 100%、平均 5.4 手就贏），繼續練只會過擬合欺負隨機棋。
2. **不能回到單一 policy 自我對弈**——專案先前已驗證會產生「合謀快速結束」的退化行為（見 `docs/RL_TRAINING_NOTES.md`）。
3. **混合對手池**（heuristic 為主 + 凍結的舊模型 + 少量 random）能同時提供：
   - 有挑戰性的訊號（heuristic）
   - 風格多樣性、避免過擬合單一對手（凍結模型 + random）
4. **熱啟動（warm start）**：從現有 5M vs-random 模型的權重繼續訓練，不用從零開始學「怎麼下合法的棋」。

### 本次新增的程式

- `train-maskable-ppo-vs-pool` CLI 指令（`src/animal_shogi_ai_lab/training/train_maskable_ppo_vs_pool.py`）
  - `--init-model`：熱啟動來源
  - `--opponent-model`：對手池中的凍結模型
  - `--w-heuristic / --w-model / --w-random`：對手池抽樣權重（每個 episode 抽一個對手）
- `OpponentPoolAgent`（`src/animal_shogi_ai_lab/agents/pool_agent.py`）：依權重逐局抽對手。
- `ModelOpponentAgent`（`src/animal_shogi_ai_lab/agents/model_agent.py`）：把凍結的 MaskablePPO 包成環境對手。
  - 注意：觀察（observation）有做視角旋轉、但動作編碼是絕對座標，所以黑方訓練的模型下白棋時，
    需把合法手 mask 鏡射進模型的自我視角、預測後再鏡射回來（`mirror_action`，在 `training/adapter.py`）。
- `evaluate-model --opponent heuristic`：評估功能現在支援 random 與 heuristic 兩種對手（Phase 9D 第 1 項）。

---

## 3. 已啟動的訓練（放著跑）

```bash
animal-shogi-lab train-maskable-ppo-vs-pool \
  --side BLACK \
  --timesteps 10000000 \
  --n-envs 8 \
  --seed 0 \
  --step-penalty -0.0001 \
  --init-model checkpoints/animal_shogi_maskable_ppo_vs_random/maskable_ppo_vs_random_black_20260525_140008/final_model.zip \
  --opponent-model checkpoints/animal_shogi_maskable_ppo_vs_random/maskable_ppo_vs_random_black_20260525_140008/final_model.zip \
  --w-heuristic 0.6 --w-model 0.2 --w-random 0.2
```

- 訓練 log：`runs/train_vs_pool_20260703.log`（含進度百分比與 ETA）
- checkpoint 目錄：`checkpoints/animal_shogi_maskable_ppo_vs_pool/maskable_ppo_vs_pool_black_<時間戳>/`
- 每 50,000 步自動存一個 checkpoint，中途停掉也有東西可用。
- 實測速度約 1,200+ FPS（4 envs 時），10M 步預估數小時內完成。

---

## 4. 回來之後的檢查清單

1. **看訓練進度 / 是否完成**：

   ```bash
   tail -20 runs/train_vs_pool_20260703.log
   ```

2. **評估新模型**（把 `<run>` 換成實際目錄名）：

   ```bash
   animal-shogi-lab evaluate-model --model checkpoints/animal_shogi_maskable_ppo_vs_pool/<run>/final_model.zip --games 200 --side BLACK --opponent heuristic
   animal-shogi-lab evaluate-model --model checkpoints/animal_shogi_maskable_ppo_vs_pool/<run>/final_model.zip --games 200 --side BLACK --opponent random
   ```

   判讀標準：
   - 對 heuristic 勝率 **> 50%**：大成功，直接上介面對弈。
   - 對 heuristic 勝率 **10%–50%**：有進步，可加長訓練或做第二輪迭代（見第 5 節）。
   - 對 heuristic 勝率仍接近 **0%**：熱啟動可能被舊策略卡住，改成不帶 `--init-model` 從零開始
     純 vs-heuristic 訓練（`train-maskable-ppo-vs-heuristic`）再比較。
   - 對 random 勝率若明顯掉到 90% 以下：代表有遺忘（forgetting），可把 `--w-random` 調高一點重跑。

3. **親自上介面對弈**：

   ```bash
   animal-shogi-lab debug-board --model checkpoints/animal_shogi_maskable_ppo_vs_pool/<run>/final_model.zip --ai-side BLACK
   ```

4. **把結果記到 `docs/EXPERIMENTS.md`**（已預留條目格式）。

---

## 5. 之後的方向（本輪完成後）

依優先順序：

1. **自我對弈迭代（iterated self-play）**：把這一輪練出來的最強模型「凍結」放進對手池，
   再訓練下一代（v2 → v3 → …）。每一代都用固定的評估組（random / heuristic / 上一代模型）量勝率，
   確保是真變強、不是互相過擬合。指令上就是把 `--opponent-model` 換成新模型、`--init-model` 也換成新模型。
2. **checkpoint 比較**（Phase 9D 第 3 項）：比較 1M/3M/5M/10M checkpoint 對 heuristic 的勝率，找出高原點。
3. **白棋側**：目前只訓練黑方。介面上若想讓 AI 執白，建議另外訓練一個 `--side WHITE` 的模型
   （注意：動作編碼是絕對座標，黑方模型不能直接當白棋用；`ModelOpponentAgent` 的鏡射邏輯只用於訓練時的對手）。
4. **更強的對手**：等模型穩定壓制一層 heuristic 後，實作二層（two-ply）heuristic 或淺層 MCTS 當新對手。
5. **獎勵微調**：只有在觀察到明確問題（例如龜縮不進攻）才加小幅 shaping，原則見 `docs/NEXT_TRAINING_STEPS.md` 的 Phase 9E。

---

## 6. 防呆備忘

- 不要回到「一個 policy 同時控制雙方」的自我對弈。
- 不要 commit `checkpoints/`、`runs/` 等產出物。
- 每次改訓練設定前，先用固定評估組量一次基準，改完再量一次，數字進 `docs/EXPERIMENTS.md`。
- 驗證指令（commit 前必跑）：

  ```bash
  python -m ruff check src tests
  python -m compileall src
  python -m pytest
  ```

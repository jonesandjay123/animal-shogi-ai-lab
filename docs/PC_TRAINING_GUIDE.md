# PC 強化學習訓練操作手冊

本手冊為您詳細說明如何將本專案轉移到有顯卡（GPU）的 PC 上進行架設、安裝依賴、啟動訓練、查看即時進度以及訓練完成後的評估與對戰。

---

## 步驟 1：複製專案與目錄準備
在您的 PC 終端機（如 Git Bash, Windows Terminal 或 Linux Terminal）中執行：
```bash
# 複製您的專案庫（請替換為您正確的 git 網址）
git clone https://github.com/jonesandjay123/animal-shogi-ai-lab.git
cd animal-shogi-ai-lab
```

---

## 步驟 2：建立虛擬環境 (venv)
建議使用獨立的 Python 虛擬環境，避免套件版本衝突（請確保 Python 版本 $\ge 3.10$，本專案推薦使用 Python 3.11 或 3.13）：
```bash
python3 -m venv .venv
```

---

## 步驟 3：啟用虛擬環境
依據您 PC 的作業系統與使用的終端機，執行對應的啟用指令：

* **Linux / macOS / Windows Git Bash / WSL**：
  ```bash
  source .venv/bin/activate
  ```
* **Windows PowerShell**：
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
* **Windows CMD (命令提示字元)**：
  ```cmd
  .venv\Scripts\activate.bat
  ```

---

## 步驟 4：安裝專案與強化學習依賴包
啟用虛擬環境後，執行以下一鍵安裝指令（這會安裝開發、UI 及強化學習所需的所有套件，包括 PyTorch、Gymnasium 與 stable-baselines3）：
```bash
pip install -e ".[dev,ui,rl]"
```

*(選用) 如果您的 PC 是 Windows 且有 NVIDIA 獨立顯卡，建議至 [PyTorch 官網](https://pytorch.org/) 取得符合您 CUDA 版本的獨立安裝指令。例如：*
```bash
# （選用：僅適用於 Windows/CUDA 12.1 的 PyTorch 安裝指令）
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

---

## 步驟 5：檢查 GPU 是否啟用成功
執行以下快速指令，確認 PyTorch 能正確偵測到您的 NVIDIA 顯卡：
```bash
python -c "import torch; print('CUDA 是否可用:', torch.cuda.is_available()); print('目前使用裝置:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```
* **成功畫面**：應顯示 `CUDA 是否可用: True`，且設備名稱會顯示如 `NVIDIA GeForce RTX 5080`（或您的顯卡型號）。

---

## 步驟 6：執行單元測試驗證
在訓練前，執行測試套件以確保所有功能皆正常：
```bash
pytest
```
* 應該顯示 **58 passed** 綠色字樣，代表引擎、環境與適配器皆完全正常。

---

## 步驟 7：啟動對抗訓練 (vs Random)

使用我們最新設計的對抗模式進行訓練。以下以**黑棋 (BLACK)** 為訓練視角，跑 **500 萬步** 為例：

```bash
# 在背景啟動訓練 (適用於 Linux / Git Bash / macOS)
nohup animal-shogi-lab train-maskable-ppo-vs-random --side BLACK --timesteps 5000000 --n-envs 8 --seed 0 > runs/maskable_ppo_vs_random.log 2>&1 &
```
* `--side BLACK`：代表 AI 控制黑棋，對手白棋為隨機下棋的 `RandomAgent`（您也可以訓練 `--side WHITE`）。
* `--timesteps 5000000`：設定訓練步數為 5,000,000 步。
* `--n-envs 8`：開啟 8 個並行環境，充分發揮 CPU 多核心效能。

---

## 步驟 8：即時監看進度、估計剩餘時間 (ETA)

我們為您設計了專用的 `ProgressEstimatorCallback` 進度監看器。

您可以隨時輸入以下指令來查看即時日誌：
```bash
tail -f runs/maskable_ppo_vs_random.log
```

您將會看到非常直觀的進度條：
```text
[Progress]  12.5% | Steps: 625,000 / 5,000,000 | FPS: 7850 | Elapsed: 00:01:19 | ETA: 00:09:17
[Progress]  15.0% | Steps: 750,000 / 5,000,000 | FPS: 7890 | Elapsed: 00:01:35 | ETA: 00:08:58
```
* **百分比** (如 `15.0%`)：目前訓練的總進度。
* **Steps** (如 `750,000 / 5,000,000`)：已執行的步數與目標步數。
* **FPS** (如 `7890`)：每秒的運算步數。
* **Elapsed** (如 `00:01:35`)：已經訓練花費的時間。
* **ETA** (如 `00:08:58`)：**預估剩下的訓練時間**（格式為 時:分:秒）。

*(按 `Ctrl + C` 可以退出監看，不會影響背景訓練。)*

---

## 步驟 9：訓練完成後的對戰與評估

訓練結束後，模型檔會存放在 `checkpoints/animal_shogi_maskable_ppo_vs_random/` 目錄下。

### 1. 勝率自動化評估
使用命令行工具測試您訓練的黑棋模型對戰隨機對手的勝率：
```bash
animal-shogi-lab evaluate-model --model checkpoints/animal_shogi_maskable_ppo_vs_random/maskable_ppo_vs_random_<時間戳記>/final_model.zip --games 100 --side BLACK --opponent random
```

### 2. 在 Pygame 中親自與 AI 對決
您可以親自扮演白棋，挑戰剛訓練好的黑棋 AI：
```bash
animal-shogi-lab debug-board --model checkpoints/animal_shogi_maskable_ppo_vs_random/maskable_ppo_vs_random_<時間戳記>/final_model.zip --ai-side BLACK
```
* 這會開啟 Pygame 視窗，AI (BLACK) 會先下第一步，接著換您點擊棋子進行操作。

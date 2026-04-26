# Setup Guide — ODSC East 2026 Tutorial

**Spec-Driven Simulation Modeling: Building and Validating Decision Support Models with Python and LLMs**

This is a hands-on workshop. Please do this 15-minute setup *before* the session — there isn't time to debug environment issues during the tutorial.

You have two paths. Pick whichever is easier for you. Both run the same notebooks against the same data.

---

## Path A — Local Jupyter (recommended)

If you already have Python and Jupyter on your laptop, this is the lowest-friction path. Everything runs offline once installed.

### What you need

- Python 3.10 or newer.
- About 200 MB of disk space for the workshop folder and dependencies.
- Roughly 10 minutes to install and verify.

### Steps

Open a terminal in the workshop folder (`ODSC East 2026/`) and run:

```bash
python -m venv .venv
source .venv/bin/activate         # macOS / Linux
# .venv\Scripts\activate          # Windows PowerShell
pip install -r requirements.txt
jupyter notebook
```

Then open `notebooks/00_verify_setup.ipynb` in your browser and run all cells. Every cell should print a green check or `OK`. If any cell errors out, see [Troubleshooting](#troubleshooting) below.

### What gets installed

The packages in `requirements.txt`: NumPy, SciPy, pandas, matplotlib, SimPy, Jupyter, plus the optional Anthropic SDK for the live LLM cell in Block 5. Total install footprint is about 350 MB.

---

## Path B — Google Colab (no install)

If you don't want to set up a local environment, use Colab. Everything runs in your browser. The trade-off is that you need internet during the workshop and Colab will lose your work if the runtime restarts.

### Steps

1. Open the shared workshop folder on Google Drive: [bit.ly/4tL4uvW](https://bit.ly/4tL4uvW) (full link: [odsc-east-2026 on Google Drive](https://drive.google.com/drive/folders/1nhCLEMUgZtOlxXY7rKAr2_i9NaRKGOml?usp=sharing)).
2. Add it to your own Drive so Colab can read and write the files. From the folder view, click the folder name at the top → **Organize** → **Add shortcut** → choose **My Drive**.
3. In Colab, mount your Drive and install dependencies:
   ```python
   from google.colab import drive
   drive.mount('/content/drive')
   %cd /content/drive/MyDrive/odsc-east-2026
   !pip install -r requirements.txt
   ```
4. Open `notebooks/00_verify_setup.ipynb` from the Drive folder (right-click → **Open with → Google Colaboratory**) and run all cells.

If everything passes, you are set.

### Notes

The Colab path uses the same notebooks and the same data as the local path — the Drive folder is a copy of the workshop repo. If you want to edit a notebook without affecting the shared copy, use **File → Save a copy in Drive** in Colab, which forks it into your own Drive.

---

## What to do before the workshop starts

Run **`notebooks/00_verify_setup.ipynb`** end-to-end. All cells should pass. If any fail, fix them before the session — that notebook is the same set of imports the rest of the workshop depends on.

You do **not** need to run any of the other notebooks before the session. We work through them together.

---

## Optional — the live LLM cell

Block 5 contains one cell that calls Anthropic's API to do an LLM-assisted spec compliance review. It also ships with a *saved response fallback* that runs the same exercise without any API call.

The default and recommended path is the fallback. The exercise produces identical output and removes a failure mode (network, key issues, rate limits) that is unhelpful in a workshop setting.

If you do want to run the live call:

1. Get an API key from [console.anthropic.com](https://console.anthropic.com).
2. Set it in your environment before launching Jupyter:
   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...
   jupyter notebook
   ```
3. The cell will print `Source: live_api` instead of `Source: saved_fallback`.

---

## Troubleshooting

**`pip install` fails on macOS with a permissions error.** Use the virtual environment as shown above, or add `--user` to the install command. Don't use `sudo` with `pip`.

**`jupyter` command not found after install.** Your virtual environment isn't active. Re-run `source .venv/bin/activate` (or the Windows equivalent) and try again.

**SimPy install errors with a compiler complaint.** Upgrade pip first: `pip install --upgrade pip`, then retry. SimPy is pure Python and shouldn't need a compiler; this error means an older pip is trying to build a binary that has a wheel.

**The verification notebook says "data file not found".** The dataset lives at `data/coffee_shop_pos.csv` relative to the workshop folder. If you cloned or downloaded the workshop to a different layout, adjust the `DATA_PATH` constant in the verification notebook's first cell.

**Colab says "no module named simpy" after running the bootstrap cell.** Restart the Colab runtime (Runtime → Restart) and re-run the bootstrap cell. Colab sometimes caches the previous session's package state.

**You're stuck.** Email dan@sullivanlearninggroup.com with the error message. The setup is the riskiest part of the workshop and getting unstuck before the session is much faster than during.

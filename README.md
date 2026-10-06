# Powerball Toolkit

[한국어 README](README.ko.md)

A small Python program that does three things:

1. **Generate** random Powerball numbers (5 white balls from 1-69 + 1 Powerball from 1-26)
2. **Analyze** past winning numbers (frequency, longest-unseen numbers, chi-square uniformity test)
3. **Compare** a simulated draw against the real history in an interactive chart

```
[Set 1]
+----+----+----+----+----+   +----+
| 05 | 13 | 16 | 24 | 62 |   | 07 |
+----+----+----+----+----+   +----+
  White balls               Powerball
```

> **Please note:** every drawing is independent. "Hot" or "overdue" numbers are no more likely to come up next, and this tool cannot predict results. It is meant for learning, statistics practice, and simulation.

## Files

| File | Description |
|---|---|
| `powerball_en.py` | English version |
| `powerball.py` | Korean version (same features) |
| `requirements.txt` | Python packages to install |
| `LICENSE` | MIT License |

## Quick start (first-time users)

### 1. Install Python

Open a terminal and check whether Python is already installed:

```bash
python --version      # Windows
python3 --version     # macOS / Linux
```

You need **Python 3.8 or newer**. If you see "command not found", download it from <https://www.python.org/downloads/>.
On Windows, tick **"Add python.exe to PATH"** in the installer.

> **How to open a terminal:** Windows - search for "Command Prompt" or "PowerShell". macOS - open "Terminal" from Spotlight. Linux - `Ctrl + Alt + T`.

### 2. Download this project

With Git:

```bash
git clone https://github.com/tarsian/Try_Your_Powerball_Drawing.git
cd Try_Your_Powerball_Drawing
```

Or click **Code > Download ZIP** on GitHub, unzip it, and `cd` into the folder.

### 3. Install the required packages

```bash
pip install -r requirements.txt
```

Or install them one by one:

```bash
pip install pandas requests matplotlib scipy
```

If `pip` is not found, use this instead (it also avoids "wrong Python" problems):

```bash
python -m pip install -r requirements.txt
```

What each package is for:

| Package | Needed for |
|---|---|
| `pandas` | statistics (`stats`, `compare`) |
| `requests` | downloading data from the API |
| `matplotlib` | the chart (`compare`) |
| `scipy` | p-value in the chi-square test (optional, everything else works without it) |

The `draw` command needs **no packages at all**.

### 4. Run it

```bash
python powerball_en.py
```

Running without a command opens a simple menu:

```
===== Powerball =====
1) Draw numbers   2) Historical stats   3) Actual vs. simulation chart   0) Quit
```

> On macOS / Linux use `python3` instead of `python`.

## Commands

```bash
python powerball_en.py draw             # 1 set of numbers
python powerball_en.py draw -n 5        # 5 sets
python powerball_en.py stats            # statistics of the last 5 years
python powerball_en.py stats --years 3  # last 3 years
python powerball_en.py stats --years 0  # everything since 2015-10-07
python powerball_en.py compare          # chart: actual vs. simulated
```

### Options for `stats` and `compare`

| Option | Default | Description |
|---|---|---|
| `--years N` | `5` | Use only the last N years from today (`0` = all data) |
| `--csv FILE` | (API) | Use a CSV downloaded from powerball.com instead of the API |
| `--date-col NAME` | `Draw Date` | Name of the date column in your CSV |
| `--num-col NAME` | `Winning Numbers` | Name of the numbers column in your CSV |

You can also change the default window by editing `YEARS = 5` near the top of the script.

## What you get

**`stats`** prints:
- the 10 most frequent white balls and 5 most frequent Powerballs
- a grid of every number with its count (`+` = top 5, `-` = bottom 5)
- the numbers that have gone the longest without being drawn
- a chi-square test of whether the history looks uniform

**`compare`** opens a chart with the real counts next to a simulation of the same number of drawings.
- Every number is shown on the x-axis, and counts are whole numbers.
- **Hover over a bar** to see its number and count.
- The chart is also saved as `powerball_compare_en.png` (without the hover tooltips).

## Data source

Winning numbers come from the New York State open data portal:

```
https://data.ny.gov/api/v3/views/d6yy-54nr/query.json
```

Only drawings since **2015-10-07** are used, because the number ranges changed on that date (white balls 1-69, Powerball 1-26).

## Troubleshooting

| Problem | Fix |
|---|---|
| `python` is not recognized | Use `python3`, or reinstall Python and tick "Add to PATH" |
| `pip` is not recognized | Run `python -m pip install -r requirements.txt` |
| `ModuleNotFoundError: No module named 'matplotlib'` (or pandas, requests) | Install it with `pip install matplotlib` |
| `error: the following arguments are required: cmd` | You are running an old version; use the latest file (running without a command opens the menu) |
| Cannot download data / connection error | Check your internet connection, or download a CSV from powerball.com and run `python powerball_en.py stats --csv your_file.csv` |
| No chart window appears (VS Code) | Run it from a terminal instead: `python powerball_en.py compare` |
| Korean version shows broken characters in the chart | Install a Korean font (Malgun Gothic / AppleGothic / NanumGothic), or use the English version |

## Disclaimer

This is an independent hobby project. It is not affiliated with or endorsed by Powerball, the Multi-State Lottery Association, or any lottery operator. It does not predict winning numbers, and it is not intended for operating or promoting gambling services.

## License

This project is released under the [MIT License](LICENSE).

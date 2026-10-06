#!/usr/bin/env python3
"""Powerball number generator + historical statistics + simulation comparison

Usage:
  python powerball_en.py draw [-n 5]                  Generate numbers (default: 1 set)
  python powerball_en.py stats [--csv file.csv]       Statistics of past winning numbers
  python powerball_en.py compare [--csv file.csv]     Simulation vs. actual distribution (chart)
  python powerball_en.py                              Interactive menu

Data: https://data.ny.gov/api/v3/views/d6yy-54nr/query.json (New York State open data)
Requires: pip install pandas requests matplotlib scipy   (scipy is optional)
"""
import argparse
import random
from collections import Counter

# Current US Powerball format (since the 2015-10-07 drawing)
WHITE_MAX, WHITE_COUNT, POWER_MAX = 69, 5, 26
RULE_START = "2015-10-07"
NY_API = "https://data.ny.gov/api/v3/views/d6yy-54nr/query.json"
PAGE_SIZE = 1000
YEARS = 5  # Statistics window: the last N years counting back from today


# ---------- Cell-style output ----------
def cells_row(items, width=4):
    """['03','07'] -> three-line string with each item in its own cell"""
    line = "+" + "+".join("-" * width for _ in items) + "+"
    body = "|" + "|".join(f"{x:^{width}}" for x in items) + "|"
    return f"{line}\n{body}\n{line}"


def show_ticket(whites, power, label=""):
    """Print a draw result in cells: 5 white-ball cells + 1 Powerball cell"""
    w = cells_row([f"{n:02d}" for n in whites]).split("\n")
    p = cells_row([f"{power:02d}"]).split("\n")
    if label:
        print(label)
    for a, b in zip(w, p):
        print(a + "   " + b)
    print("  White balls" + " " * (len(w[0]) - 11) + "Powerball")


def show_grid(counter, max_num, cols, title, mark=5):
    """Lay out numbers 1..max_num in cells and show each number's count.
    The top `mark` most frequent numbers get '+', the `mark` least frequent get '-'."""
    ranked = sorted(range(1, max_num + 1), key=lambda n: (counter.get(n, 0), n))
    low = set(ranked[:mark])
    high = set(ranked[-mark:])
    width = 6
    print(f"\n== {title} (cell: top=number, bottom=count / + top {mark}, - bottom {mark}) ==")
    sep = "+" + "+".join("-" * width for _ in range(cols)) + "+"
    for start in range(1, max_num + 1, cols):
        nums = list(range(start, min(start + cols, max_num + 1)))
        top = "|" + "|".join(f"{n:02d}".center(width) for n in nums)
        bot = "|"
        for n in nums:
            c = counter.get(n, 0)
            m = "+" if n in high else "-" if n in low else " "
            bot += f"{c}{m}".center(width) + "|"
        # Pad the last row with empty cells
        pad = cols - len(nums)
        top += "|" + "|".join(" " * width for _ in range(pad)) + "|" if pad else "|"
        bot += "|".join(" " * width for _ in range(pad)) + ("|" if pad else "")
        print(sep)
        print(top)
        print(bot)
    print(sep)


# ---------- Drawing ----------
def draw_once():
    whites = sorted(random.sample(range(1, WHITE_MAX + 1), WHITE_COUNT))
    power = random.randint(1, POWER_MAX)
    return whites, power


# ---------- Data loading ----------
def parse(df, date_col, num_col):
    import pandas as pd
    df = df.copy()
    df["date"] = pd.to_datetime(df[date_col])
    nums = df[num_col].astype(str).str.split()
    df["whites"] = nums.apply(lambda x: sorted(map(int, x[:5])))
    df["power"] = nums.apply(lambda x: int(x[5]))
    df = df[df["date"] >= RULE_START].sort_values("date").reset_index(drop=True)
    return df[["date", "whites", "power"]]


def fetch_api_rows(url=NY_API, page_size=PAGE_SIZE, max_pages=200):
    """Fetch all rows from the NY open-data v3 query.json endpoint, page by page.

    The response looks like [{"draw_date": ..., "winning_numbers": "02 21 24 25 64 07", ...}, ...].
    If the server ignores the paging parameters and keeps returning the same rows,
    duplicates are filtered out by row id and the loop stops.
    """
    import requests
    rows, seen = [], set()
    for page in range(1, max_pages + 1):
        resp = requests.get(url, params={"pageNumber": page, "pageSize": page_size}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list) or not data:
            break
        new = [r for r in data if r.get(":id", id(r)) not in seen]
        if not new:  # no new rows -> stop (in case paging params are unsupported)
            break
        seen.update(r.get(":id", id(r)) for r in new)
        rows.extend(new)
        if len(data) < page_size:
            break
    return rows


def load_data(csv_path=None, date_col="Draw Date", num_col="Winning Numbers", years=YEARS):
    """Load data and keep only drawings from the last `years` years (None/0 = all)."""
    import pandas as pd
    if csv_path:
        df = parse(pd.read_csv(csv_path), date_col, num_col)
    else:
        rows = fetch_api_rows()
        if not rows:
            raise RuntimeError("No data was received from the API.")
        df = parse(pd.DataFrame(rows), "draw_date", "winning_numbers")
    if years:
        cutoff = pd.Timestamp.today().normalize() - pd.DateOffset(years=years)
        df = df[df["date"] >= cutoff].reset_index(drop=True)
        if df.empty:
            raise RuntimeError(f"No data found within the last {years} years.")
    return df


# ---------- Statistics ----------
def count_numbers(df):
    white_cnt = Counter(x for w in df["whites"] for x in w)
    power_cnt = Counter(df["power"])
    return white_cnt, power_cnt


def frequency_table(counter, max_num, draws, per_draw):
    import pandas as pd
    expected = draws * per_draw / max_num
    rows = [{"Number": n, "Count": counter.get(n, 0), "Expected": round(expected, 1)}
            for n in range(1, max_num + 1)]
    return pd.DataFrame(rows).sort_values("Count", ascending=False)


def overdue(df, col, max_num, is_list):
    import pandas as pd
    last = {}
    for i, v in enumerate(df[col]):
        for n in (v if is_list else [v]):
            last[n] = i
    total = len(df)
    rows = [{"Number": n, "Draws since last seen": total - 1 - last[n] if n in last else total}
            for n in range(1, max_num + 1)]
    return pd.DataFrame(rows).sort_values("Draws since last seen", ascending=False)


def chi_square(counter, max_num, draws, per_draw):
    expected = draws * per_draw / max_num
    stat = sum((counter.get(n, 0) - expected) ** 2 / expected for n in range(1, max_num + 1))
    try:
        from scipy.stats import chi2
        p = 1 - chi2.cdf(stat, max_num - 1)
    except ImportError:
        p = None
    return stat, p


def run_stats(df):
    n = len(df)
    print(f"Analyzed: {n} drawings ({df['date'].min().date()} to {df['date'].max().date()})\n")
    white_cnt, power_cnt = count_numbers(df)

    print("== Top 10 white balls ==")
    print(frequency_table(white_cnt, WHITE_MAX, n, WHITE_COUNT).head(10).to_string(index=False))
    print("\n== Top 5 Powerballs ==")
    print(frequency_table(power_cnt, POWER_MAX, n, 1).head(5).to_string(index=False))
    show_grid(white_cnt, WHITE_MAX, 10, "White ball frequency by number")
    show_grid(power_cnt, POWER_MAX, 13, "Powerball frequency by number")

    print("\n== Top 5 white balls not seen for the longest ==")
    print(overdue(df, "whites", WHITE_MAX, True).head(5).to_string(index=False))
    print("\n== Top 5 Powerballs not seen for the longest ==")
    print(overdue(df, "power", POWER_MAX, False).head(5).to_string(index=False))

    for name, cnt, mx, per in [("White balls", white_cnt, WHITE_MAX, WHITE_COUNT),
                               ("Powerball", power_cnt, POWER_MAX, 1)]:
        stat, p = chi_square(cnt, mx, n, per)
        p_txt = "scipy not installed" if p is None else f"{p:.3f}"
        print(f"\n{name} uniformity test: chi2={stat:.1f}, p={p_txt}")
    print("\nNote: a large p-value means the data is consistent with a uniform (fair) draw.")


# ---------- Simulation comparison ----------
def attach_hover(fig, ax_items):
    """Show a tooltip with 'number / count' when the mouse is over a bar.
    ax_items: [(ax, [(rect, number, label), ...]), ...]"""
    annots = {}
    for ax, _ in ax_items:
        a = ax.annotate("", xy=(0, 0), xytext=(12, 18), textcoords="offset points",
                        bbox=dict(boxstyle="round", fc="lightyellow", ec="gray"),
                        arrowprops=dict(arrowstyle="->"), zorder=10)
        a.set_visible(False)
        annots[ax] = a

    def on_move(event):
        changed = False
        for ax, bars in ax_items:
            annot = annots[ax]
            hit = None
            if event.inaxes is ax:
                for rect, num, label in bars:
                    if rect.contains(event)[0]:
                        hit = (rect, num, label)
                        break
            if hit:
                rect, num, label = hit
                annot.xy = (rect.get_x() + rect.get_width() / 2, rect.get_height())
                annot.set_text(f"Number {num}\n{label}: {int(rect.get_height())} times")
                annot.set_visible(True)
                changed = True
            elif annot.get_visible():
                annot.set_visible(False)
                changed = True
        if changed:
            fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", on_move)
    return on_move


def run_compare(df, out="powerball_compare_en.png"):
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator
    n = len(df)
    real_w, real_p = count_numbers(df)

    sim_w, sim_p = Counter(), Counter()
    for _ in range(n):  # simulate the same number of drawings as the real data
        w, p = draw_once()
        sim_w.update(w)
        sim_p[p] += 1

    fig, axes = plt.subplots(2, 1, figsize=(14, 8))
    ax_items = []
    for ax, real, sim, mx, title in [
        (axes[0], real_w, sim_w, WHITE_MAX, "White balls (1-69)"),
        (axes[1], real_p, sim_p, POWER_MAX, "Powerball (1-26)"),
    ]:
        xs = list(range(1, mx + 1))
        b_real = ax.bar([x - 0.2 for x in xs], [real.get(x, 0) for x in xs], width=0.4, label="Actual")
        b_sim = ax.bar([x + 0.2 for x in xs], [sim.get(x, 0) for x in xs], width=0.4, label="Simulated")
        ax.set_title(f"{title} - frequency ({n} drawings)")
        ax.set_xlabel("Number")
        ax.set_ylabel("Times drawn")
        # Show every number as an integer / integer-only count ticks
        ax.set_xticks(xs)
        ax.set_xticklabels([str(x) for x in xs], fontsize=7 if mx > 30 else 9)
        ax.set_xlim(0.3, mx + 0.7)
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax.legend()
        bars = [(r, x, "Actual") for r, x in zip(b_real, xs)] + \
               [(r, x, "Simulated") for r, x in zip(b_sim, xs)]
        ax_items.append((ax, bars))

    plt.tight_layout()
    plt.savefig(out, dpi=150)
    print(f"Chart saved: {out}")
    attach_hover(fig, ax_items)  # hover over a bar to see number / count
    plt.show()


# ---------- Entry point ----------
def menu():
    """Menu shown when run without a command (e.g. pressing F5 in VS Code)"""
    while True:
        print("\n===== Powerball =====")
        print("1) Draw numbers   2) Historical stats   3) Actual vs. simulation chart   0) Quit")
        choice = input("Choose: ").strip()
        if choice == "1":
            n = input("How many sets? (default 1): ").strip()
            for i in range(int(n) if n.isdigit() else 1):
                w, p = draw_once()
                show_ticket(w, p, f"[Set {i + 1}]")
        elif choice == "2":
            run_stats(load_data())
        elif choice == "3":
            run_compare(load_data())
        elif choice == "0":
            break


def main():
    ap = argparse.ArgumentParser(description="Powerball generator / statistics")
    sub = ap.add_subparsers(dest="cmd")  # command is optional -> falls back to the menu

    d = sub.add_parser("draw", help="generate numbers")
    d.add_argument("-n", type=int, default=1, help="number of sets")

    for name in ("stats", "compare"):
        s = sub.add_parser(name)
        s.add_argument("--csv", help="path to a CSV from powerball.com (omit to use the API)")
        s.add_argument("--date-col", default="Draw Date")
        s.add_argument("--num-col", default="Winning Numbers")
        s.add_argument("--years", type=int, default=YEARS,
                       help=f"use only the last N years (default {YEARS}, 0 = all)")

    args = ap.parse_args()

    if args.cmd is None:
        menu()
        return

    if args.cmd == "draw":
        for i in range(args.n):
            w, p = draw_once()
            show_ticket(w, p, f"[Set {i + 1}]")
        return

    df = load_data(args.csv, args.date_col, args.num_col, args.years)
    if args.cmd == "stats":
        run_stats(df)
    else:
        run_compare(df)


if __name__ == "__main__":
    main()

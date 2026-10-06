#!/usr/bin/env python3
"""파워볼 번호 추첨기 + 과거 당첨 번호 통계 + 시뮬레이션 비교

사용법:
  python powerball.py draw [-n 5]                 번호 추첨 (기본 1세트)
  python powerball.py stats [--csv 파일.csv]       과거 당첨 번호 통계
  python powerball.py compare [--csv 파일.csv]     시뮬레이션 vs 실제 분포 비교 (그래프)

데이터: https://data.ny.gov/api/v3/views/d6yy-54nr/query.json (NY주 공공데이터)
필요 라이브러리: pip install pandas requests matplotlib scipy  (scipy는 선택)
"""
import argparse
import random
from collections import Counter

# 현행 미국 파워볼 규격 (2015-10-07 추첨부터)
WHITE_MAX, WHITE_COUNT, POWER_MAX = 69, 5, 26
RULE_START = "2015-10-07"
NY_API = "https://data.ny.gov/api/v3/views/d6yy-54nr/query.json"
PAGE_SIZE = 1000
YEARS = 5  # 통계에 사용할 기간: 오늘로부터 최근 N년


# ---------- 셀(칸) 출력 ----------
def cells_row(items, width=4):
    """['03','07'] -> 칸으로 감싼 3줄 문자열"""
    line = "+" + "+".join("-" * width for _ in items) + "+"
    body = "|" + "|".join(f"{x:^{width}}" for x in items) + "|"
    return f"{line}\n{body}\n{line}"


def show_ticket(whites, power, label=""):
    """추첨 결과를 칸 안에 정렬해서 출력: 흰 공 5칸 + 파워볼 1칸"""
    w = cells_row([f"{n:02d}" for n in whites]).split("\n")
    p = cells_row([f"{power:02d}"]).split("\n")
    if label:
        print(label)
    for a, b in zip(w, p):
        print(a + "   " + b)
    print("  흰 공" + " " * (len(w[0]) - 4) + "파워볼")


def show_grid(counter, max_num, cols, title, mark=5):
    """번호 1~max_num을 칸에 배치하고 칸마다 출현 횟수를 표시.
    많이 나온 상위 mark개는 '+', 적게 나온 하위 mark개는 '-'를 붙인다."""
    ranked = sorted(range(1, max_num + 1), key=lambda n: (counter.get(n, 0), n))
    low = set(ranked[:mark])
    high = set(ranked[-mark:])
    width = 6
    print(f"\n== {title} (칸: 위=번호, 아래=횟수 / + 상위{mark}, - 하위{mark}) ==")
    sep = "+" + "+".join("-" * width for _ in range(cols)) + "+"
    for start in range(1, max_num + 1, cols):
        nums = list(range(start, min(start + cols, max_num + 1)))
        top = "|" + "|".join(f"{n:02d}".center(width) for n in nums)
        bot = "|"
        for n in nums:
            c = counter.get(n, 0)
            m = "+" if n in high else "-" if n in low else " "
            bot += f"{c}{m}".center(width) + "|"
        # 마지막 줄이 짧으면 빈 칸으로 맞춤
        pad = cols - len(nums)
        top += "|" + "|".join(" " * width for _ in range(pad)) + "|" if pad else "|"
        bot += "|".join(" " * width for _ in range(pad)) + ("|" if pad else "")
        print(sep)
        print(top)
        print(bot)
    print(sep)


# ---------- 추첨 ----------
def draw_once():
    whites = sorted(random.sample(range(1, WHITE_MAX + 1), WHITE_COUNT))
    power = random.randint(1, POWER_MAX)
    return whites, power


# ---------- 데이터 로딩 ----------
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
    """NY 공공데이터 v3 query.json에서 전체 행을 가져온다 (페이지 단위).

    응답은 [{"draw_date": ..., "winning_numbers": "02 21 24 25 64 07", ...}, ...] 형태.
    서버가 페이지 파라미터를 무시해 같은 행이 반복되면 중복을 걸러내고 멈춘다.
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
        if not new:  # 새 행이 없으면 종료 (페이지 파라미터 미지원 대비)
            break
        seen.update(r.get(":id", id(r)) for r in new)
        rows.extend(new)
        if len(data) < page_size:
            break
    return rows


def load_data(csv_path=None, date_col="Draw Date", num_col="Winning Numbers", years=YEARS):
    """데이터를 불러와 오늘로부터 최근 years년 이내 회차만 남긴다 (years=None이면 전체)."""
    import pandas as pd
    if csv_path:
        df = parse(pd.read_csv(csv_path), date_col, num_col)
    else:
        rows = fetch_api_rows()
        if not rows:
            raise RuntimeError("API에서 데이터를 받지 못했습니다.")
        df = parse(pd.DataFrame(rows), "draw_date", "winning_numbers")
    if years:
        cutoff = pd.Timestamp.today().normalize() - pd.DateOffset(years=years)
        df = df[df["date"] >= cutoff].reset_index(drop=True)
        if df.empty:
            raise RuntimeError(f"최근 {years}년 이내 데이터가 없습니다.")
    return df


# ---------- 통계 ----------
def count_numbers(df):
    white_cnt = Counter(x for w in df["whites"] for x in w)
    power_cnt = Counter(df["power"])
    return white_cnt, power_cnt


def frequency_table(counter, max_num, draws, per_draw):
    import pandas as pd
    expected = draws * per_draw / max_num
    rows = [{"번호": n, "횟수": counter.get(n, 0), "기대횟수": round(expected, 1)}
            for n in range(1, max_num + 1)]
    return pd.DataFrame(rows).sort_values("횟수", ascending=False)


def overdue(df, col, max_num, is_list):
    import pandas as pd
    last = {}
    for i, v in enumerate(df[col]):
        for n in (v if is_list else [v]):
            last[n] = i
    total = len(df)
    rows = [{"번호": n, "미출현 회차": total - 1 - last[n] if n in last else total}
            for n in range(1, max_num + 1)]
    return pd.DataFrame(rows).sort_values("미출현 회차", ascending=False)


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
    print(f"분석 대상: 최근 기간 {n}회 ({df['date'].min().date()} ~ {df['date'].max().date()})\n")
    white_cnt, power_cnt = count_numbers(df)

    print("== 흰 공 상위 10 ==")
    print(frequency_table(white_cnt, WHITE_MAX, n, WHITE_COUNT).head(10).to_string(index=False))
    print("\n== 파워볼 상위 5 ==")
    print(frequency_table(power_cnt, POWER_MAX, n, 1).head(5).to_string(index=False))
    show_grid(white_cnt, WHITE_MAX, 10, "흰 공 번호별 출현 횟수")
    show_grid(power_cnt, POWER_MAX, 13, "파워볼 번호별 출현 횟수")

    print("\n== 흰 공 오래 안 나온 번호 TOP 5 ==")
    print(overdue(df, "whites", WHITE_MAX, True).head(5).to_string(index=False))
    print("\n== 파워볼 오래 안 나온 번호 TOP 5 ==")
    print(overdue(df, "power", POWER_MAX, False).head(5).to_string(index=False))

    for name, cnt, mx, per in [("흰 공", white_cnt, WHITE_MAX, WHITE_COUNT),
                               ("파워볼", power_cnt, POWER_MAX, 1)]:
        stat, p = chi_square(cnt, mx, n, per)
        p_txt = "scipy 없음" if p is None else f"{p:.3f}"
        print(f"\n{name} 균등성 검정: χ²={stat:.1f}, p={p_txt}")
    print("\n※ p값이 크면 실제 추첨이 균등하다는 가정과 모순되지 않는다는 뜻입니다.")


# ---------- 시뮬레이션 비교 ----------
def attach_hover(fig, ax_items):
    """막대 위에 마우스를 올리면 '번호 / 출현 횟수'를 말풍선으로 표시.
    ax_items: [(ax, [(rect, 번호, 라벨), ...]), ...]"""
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
                annot.set_text(f"번호 {num}\n{label}: {int(rect.get_height())}회")
                annot.set_visible(True)
                changed = True
            elif annot.get_visible():
                annot.set_visible(False)
                changed = True
        if changed:
            fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", on_move)
    return on_move


def run_compare(df, out="powerball_compare.png"):
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator
    # 한글 폰트 (Windows / macOS / Linux 순으로 있는 것을 사용)
    plt.rcParams["font.family"] = ["Malgun Gothic", "AppleGothic", "NanumGothic", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    n = len(df)
    real_w, real_p = count_numbers(df)

    sim_w, sim_p = Counter(), Counter()
    for _ in range(n):  # 실제와 같은 회차 수만큼 시뮬레이션
        w, p = draw_once()
        sim_w.update(w)
        sim_p[p] += 1

    fig, axes = plt.subplots(2, 1, figsize=(14, 8))
    ax_items = []
    for ax, real, sim, mx, title in [
        (axes[0], real_w, sim_w, WHITE_MAX, "흰 공 (1~69)"),
        (axes[1], real_p, sim_p, POWER_MAX, "파워볼 (1~26)"),
    ]:
        xs = list(range(1, mx + 1))
        b_real = ax.bar([x - 0.2 for x in xs], [real.get(x, 0) for x in xs], width=0.4, label="실제")
        b_sim = ax.bar([x + 0.2 for x in xs], [sim.get(x, 0) for x in xs], width=0.4, label="시뮬레이션")
        ax.set_title(f"{title} - 출현 횟수 ({n}회)")
        ax.set_xlabel("번호")
        ax.set_ylabel("출현 횟수(회)")
        # 번호는 1, 2, 3 ... 자연수로 전부 표시 / 횟수 눈금도 정수만
        ax.set_xticks(xs)
        ax.set_xticklabels([str(x) for x in xs], fontsize=7 if mx > 30 else 9)
        ax.set_xlim(0.3, mx + 0.7)
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax.legend()
        bars = [(r, x, "실제") for r, x in zip(b_real, xs)] + \
               [(r, x, "시뮬레이션") for r, x in zip(b_sim, xs)]
        ax_items.append((ax, bars))

    plt.tight_layout()
    plt.savefig(out, dpi=150)
    print(f"그래프 저장: {out}")
    attach_hover(fig, ax_items)  # 마우스를 올리면 번호/횟수 표시
    plt.show()


# ---------- 실행 ----------
def menu():
    """명령어 없이 실행했을 때(예: VS Code에서 F5) 나오는 메뉴"""
    while True:
        print("\n===== 파워볼 =====")
        print("1) 번호 추첨   2) 과거 통계   3) 실제 vs 시뮬레이션 그래프   0) 종료")
        choice = input("선택: ").strip()
        if choice == "1":
            n = input("몇 세트? (기본 1): ").strip()
            for i in range(int(n) if n.isdigit() else 1):
                w, p = draw_once()
                show_ticket(w, p, f"[{i + 1}세트]")
        elif choice == "2":
            run_stats(load_data())
        elif choice == "3":
            run_compare(load_data())
        elif choice == "0":
            break


def main():
    ap = argparse.ArgumentParser(description="파워볼 추첨기 / 통계")
    sub = ap.add_subparsers(dest="cmd")  # 명령어 생략 가능 -> 메뉴 실행

    d = sub.add_parser("draw", help="번호 추첨")
    d.add_argument("-n", type=int, default=1, help="세트 수")

    for name in ("stats", "compare"):
        s = sub.add_parser(name)
        s.add_argument("--csv", help="powerball.com에서 받은 CSV 경로 (없으면 API 사용)")
        s.add_argument("--date-col", default="Draw Date")
        s.add_argument("--num-col", default="Winning Numbers")
        s.add_argument("--years", type=int, default=YEARS,
                       help=f"최근 N년 데이터만 사용 (기본 {YEARS}, 0이면 전체)")

    args = ap.parse_args()

    if args.cmd is None:
        menu()
        return

    if args.cmd == "draw":
        for i in range(args.n):
            w, p = draw_once()
            show_ticket(w, p, f"[{i + 1}세트]")
        return

    df = load_data(args.csv, args.date_col, args.num_col, args.years)
    if args.cmd == "stats":
        run_stats(df)
    else:
        run_compare(df)


if __name__ == "__main__":
    main()

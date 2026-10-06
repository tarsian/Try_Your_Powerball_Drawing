# 파워볼 툴킷 (Powerball Toolkit)

[English README](README.md)

세 가지 기능을 가진 작은 파이썬 프로그램이에요.

1. **번호 추첨**: 파워볼 번호 생성 (흰 공 1~69 중 5개 + 파워볼 1~26 중 1개)
2. **과거 통계**: 지난 당첨 번호의 출현 횟수, 오래 안 나온 번호, 카이제곱 균등성 검정
3. **시뮬레이션 비교**: 실제 분포와 시뮬레이션 분포를 인터랙티브 그래프로 비교

```
[1세트]
+----+----+----+----+----+   +----+
| 05 | 13 | 16 | 24 | 62 |   | 07 |
+----+----+----+----+----+   +----+
  흰 공                      파워볼
```

> **참고:** 매 회차 추첨은 서로 독립이에요. 많이 나왔거나 오래 안 나온 번호가 다음에 더 잘 나오지 않고, 이 프로그램은 당첨 번호를 예측하지 못해요. 학습, 통계 연습, 시뮬레이션 용도로 만든 프로그램이에요.

## 파일 구성

| 파일 | 설명 |
|---|---|
| `powerball.py` | 한글 버전 |
| `powerball_en.py` | 영문 버전 (기능 동일) |
| `requirements.txt` | 설치할 파이썬 패키지 목록 |

## 빠른 시작 (처음 쓰는 분용)

### 1. 파이썬 설치

터미널을 열고 파이썬이 설치되어 있는지 확인해요.

```bash
python --version      # Windows
python3 --version     # macOS / Linux
```

**Python 3.8 이상**이 필요해요. "command not found" 같은 메시지가 나오면 <https://www.python.org/downloads/> 에서 설치하세요.
Windows는 설치 화면에서 **"Add python.exe to PATH"** 를 꼭 체크하세요.

> **터미널 여는 법:** Windows는 "명령 프롬프트" 또는 "PowerShell"을 검색해서 실행해요. macOS는 Spotlight에서 "터미널"을 열어요. Linux는 `Ctrl + Alt + T`예요.

### 2. 프로젝트 내려받기

Git을 쓰는 경우:

```bash
git clone https://github.com/tarsian/Try_Your_Powerball_Drawing.git
cd Try_Your_Powerball_Drawing
```

Git이 없다면 GitHub 페이지에서 **Code > Download ZIP**을 눌러 받고, 압축을 푼 뒤 그 폴더로 이동하세요 (`cd 폴더이름`).

### 3. 필요한 패키지 설치

```bash
pip install -r requirements.txt
```

하나씩 설치해도 돼요.

```bash
pip install pandas requests matplotlib scipy
```

`pip`가 없다고 나오면 아래처럼 실행하세요. 설치한 파이썬과 `pip`가 서로 다른 경우에도 이 방법이 잘 맞아요.

```bash
python -m pip install -r requirements.txt
```

패키지별 용도예요.

| 패키지 | 용도 |
|---|---|
| `pandas` | 통계 계산 (`stats`, `compare`) |
| `requests` | API에서 데이터 받기 |
| `matplotlib` | 그래프 (`compare`) |
| `scipy` | 카이제곱 검정의 p값 계산 (선택, 없어도 나머지는 동작) |

`draw`(추첨)는 **패키지 설치 없이** 쓸 수 있어요.

### 4. 실행

```bash
python powerball.py
```

명령어 없이 실행하면 간단한 메뉴가 떠요.

```
===== 파워볼 =====
1) 번호 추첨   2) 과거 통계   3) 실제 vs 시뮬레이션 그래프   0) 종료
```

> macOS / Linux에서는 `python` 대신 `python3`을 쓰세요. 영문 버전은 `powerball_en.py`를 실행하면 돼요.

## 명령어

```bash
python powerball.py draw             # 1세트 추첨
python powerball.py draw -n 5        # 5세트 추첨
python powerball.py stats            # 최근 5년 통계
python powerball.py stats --years 3  # 최근 3년 통계
python powerball.py stats --years 0  # 2015-10-07 이후 전체
python powerball.py compare          # 실제 vs 시뮬레이션 그래프
```

### `stats`, `compare` 옵션

| 옵션 | 기본값 | 설명 |
|---|---|---|
| `--years N` | `5` | 오늘로부터 최근 N년 데이터만 사용 (`0`이면 전체) |
| `--csv 파일` | (API 사용) | API 대신 powerball.com에서 받은 CSV 사용 |
| `--date-col 이름` | `Draw Date` | CSV의 날짜 컬럼 이름 |
| `--num-col 이름` | `Winning Numbers` | CSV의 번호 컬럼 이름 |

기본 기간은 스크립트 위쪽의 `YEARS = 5`를 고쳐서 바꿀 수도 있어요.

## 결과 설명

**`stats`** 는 아래 내용을 출력해요.
- 많이 나온 흰 공 상위 10개, 파워볼 상위 5개
- 모든 번호를 칸에 배치하고 출현 횟수를 표시한 표 (`+` 상위 5개, `-` 하위 5개)
- 가장 오래 안 나온 번호
- 과거 데이터가 균등해 보이는지 확인하는 카이제곱 검정

**`compare`** 는 실제 출현 횟수와 같은 회차 수만큼 돌린 시뮬레이션을 나란히 보여주는 그래프를 띄워요.
- 가로축에 모든 번호가 표시되고, 횟수는 정수로 나와요.
- **막대 위에 마우스를 올리면** 번호와 출현 횟수가 말풍선으로 떠요.
- 그래프는 `powerball_compare.png`로도 저장돼요 (말풍선은 이미지에 포함되지 않아요).

## 데이터 출처

당첨 번호는 미국 뉴욕주 공공데이터 포털에서 가져와요.

```
https://data.ny.gov/api/v3/views/d6yy-54nr/query.json
```

번호 범위가 바뀐 **2015-10-07 추첨부터**의 데이터만 사용해요 (흰 공 1~69, 파워볼 1~26).

## 문제 해결

| 증상 | 해결 방법 |
|---|---|
| `python`을 찾을 수 없다고 나와요 | `python3`로 실행하거나, 파이썬을 다시 설치하면서 "Add to PATH"를 체크하세요 |
| `pip`를 찾을 수 없다고 나와요 | `python -m pip install -r requirements.txt`로 실행하세요 |
| `ModuleNotFoundError: No module named 'matplotlib'` (또는 pandas, requests) | `pip install matplotlib`처럼 해당 패키지를 설치하세요 |
| `error: the following arguments are required: cmd` | 예전 버전이에요. 최신 파일을 쓰세요 (명령어 없이 실행하면 메뉴가 떠요) |
| 데이터를 받지 못해요 / 연결 오류 | 인터넷 연결을 확인하거나, powerball.com에서 CSV를 받아 `python powerball.py stats --csv 파일.csv`로 실행하세요 |
| VS Code에서 그래프 창이 안 떠요 | 터미널에서 직접 실행하세요: `python powerball.py compare` |
| 그래프의 한글이 깨져요 | 한글 폰트(맑은 고딕 / AppleGothic / 나눔고딕)를 설치하거나 영문 버전을 쓰세요 |

## 면책

개인 취미로 만든 독립 프로젝트예요. Powerball, Multi-State Lottery Association 등 어떤 복권 운영 기관과도 관련이 없고 승인받지도 않았어요. 당첨 번호를 예측하지 못하며, 도박 서비스를 운영하거나 홍보하려는 용도가 아니에요.

## 라이선스

원하는 라이선스(예: MIT)를 `LICENSE` 파일로 추가하세요.

import os
import zipfile
import requests
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd

# -------------------------------
# 기본 설정 및 상수
# -------------------------------
session = requests.Session()

korean_labels = [
    "1시간기온",
    "풍속",
    "하늘상태",
    "습도",
    "일최고기온",
    "일최저기온",
    "강수형태",
    "강수확률",
    "동서바람성분",
    "남북바람성분",
    "1시간강수량",
    "1시간적설",
    "파고",
    "풍향",
]
var_codes = [
    "TMP",
    "WSD",
    "SKY",
    "REH",
    "TMX",
    "TMN",
    "PTY",
    "POP",
    "UUU",
    "VVV",
    "PCP",
    "SNO",
    "WAV",
    "VEC",
]
COLUMN_SET = list(zip(korean_labels, var_codes))


# -------------------------------
# 헤더 생성 함수
# -------------------------------
def create_first_header(cookie: str) -> dict:
    return {
        "Accept": "text/plain, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Cookie": cookie,
        "Host": "data.kma.go.kr",
        "Origin": "https://data.kma.go.kr",
        "Referer": "https://data.kma.go.kr/data/rmt/rmtList.do?code=420&pgmNo=574",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
    }


def create_second_header(cookie: str) -> dict:
    return {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Cookie": cookie,
        "Host": "data.kma.go.kr",
        "Origin": "https://data.kma.go.kr",
        "Referer": "https://data.kma.go.kr/data/rmt/rmtList.do?code=420&pgmNo=574",
        "Sec-Fetch-Dest": "iframe",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0",
        "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
    }


# -------------------------------
# 날짜 구간 생성 함수
# -------------------------------
def generate_date_intervals(
    start_date: datetime, end_date: datetime, delta_months: int = 1
):
    intervals = []
    current_start = start_date
    while current_start < end_date:
        current_end = current_start + relativedelta(months=delta_months)
        if current_end > end_date:
            current_end = end_date
        intervals.append(
            (current_start.strftime("%Y%m%d"), current_end.strftime("%Y%m%d"))
        )
        current_start = current_end
    return intervals


# -------------------------------
# 요청 본문 생성 함수
# -------------------------------
def generate_first_request_body(
    column: tuple, start: str, end: str, stnm: str, 동코드
) -> dict:
    data_code = "424"
    return {
        "apiCd": "request420",
        "data_code": data_code,
        "hour": "",
        "pageIndex": "1",
        "from": start,
        "to": end,
        "file_size": "",
        "recordCountPerPage": "10",
        "txtVar1Nm": column[0],
        "selectType": "1",
        "startDt": start[:4],
        "startMt": start[4:6],
        "endDt": end[:4],
        "endMt": end[4:6],
        "from_": start,
        "to_": end,
        "var1": column[1],
        "var3": 동코드,
        "stnm": stnm,
        "elcd": column[0],
        "strtm": start,
        "endtm": end,
        "req_list": f"{start}|{end}|{data_code}|{column[1]}|{동코드}",
    }


def generate_second_request_body(stnm: str, column: str, start: str, end: str) -> str:
    return f"{stnm}_{column}_{start}_{end}.csv"


# -------------------------------
# 경로 및 데이터 준비
# -------------------------------
BASE_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
지역코드_파일경로 = os.path.join(BASE_SCRIPT_DIR, "지역코드.csv")
지역코드_df = pd.read_csv(지역코드_파일경로)

# ✅ 시작 기준 지역 설정
start_level1 = "서울특별시"
start_level2 = "종로구"
start_level3 = "교남동"

지역코드_df["지역키"] = (
    지역코드_df["Level1"] + "|" + 지역코드_df["Level2"] + "|" + 지역코드_df["Level3"]
)
start_key = f"{start_level1}|{start_level2}|{start_level3}"

if start_key not in 지역코드_df["지역키"].values:
    raise ValueError(f"지정한 지역 ({start_key}) 을 찾을 수 없습니다.")

start_idx = 지역코드_df[지역코드_df["지역키"] == start_key].index[0]
filtered_df = 지역코드_df.iloc[start_idx:].copy()
동_set = filtered_df[["Level1", "Level2", "Level3", "ReqList_Last"]].values.tolist()

BASE_DIR = os.path.join("data", "기상예보", "동네예보", "단기예보")
start_date_obj = datetime(2021, 7, 1)
end_date_obj = datetime(2021, 12, 31)
date_intervals = generate_date_intervals(start_date_obj, end_date_obj)

# -------------------------------
# 실행
# -------------------------------
session_str = str(input("세션을 입력하세요: "))
cookie_str = f"loginId=shdbtjd8@gmail.com; JSESSIONID={session_str}"
first_header = create_first_header(cookie_str)
second_header = create_second_header(cookie_str)

for level1, level2, level3, 동코드 in 동_set:
    dong_dir = os.path.join(BASE_DIR, level1, level2, level3)
    os.makedirs(dong_dir, exist_ok=True)

    for start_date, end_date in date_intervals:
        for column in COLUMN_SET:
            request_body = generate_first_request_body(
                column, start_date, end_date, level3, 동코드
            )
            url_generation = (
                "https://data.kma.go.kr/mypage/rmt/callDtaReqstIrods4xxNewAjax.do"
            )
            print(f"[{level3}] 요청 중: {column[0]} | {start_date} ~ {end_date}")
            session.post(url_generation, headers=first_header, data=request_body)

            url_download = "https://data.kma.go.kr/data/rmt/downloadZip.do"
            data_download = {
                "downFile": generate_second_request_body(
                    level3, column[0], start_date, end_date
                )
            }
            response_download = session.post(
                url_download, headers=second_header, data=data_download, stream=True
            )

            if response_download.status_code == 200:
                zip_filename = f"{level3}_{column[0]}_{start_date}_{end_date}.zip"
                zip_filepath = os.path.join(dong_dir, zip_filename)
                with open(zip_filepath, "wb") as f:
                    for chunk in response_download.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                print("  - 다운로드 완료:", zip_filename)

                category_dir = os.path.join(dong_dir, column[0])
                os.makedirs(category_dir, exist_ok=True)
                with zipfile.ZipFile(zip_filepath, "r") as zip_ref:
                    for info in zip_ref.infolist():
                        try:
                            fixed_filename = info.filename.encode("cp437").decode(
                                "euc-kr"
                            )
                        except Exception:
                            fixed_filename = info.filename
                        target_path = os.path.join(category_dir, fixed_filename)
                        with open(target_path, "wb") as out_file:
                            out_file.write(zip_ref.read(info.filename))
                        print("    └ 추출 완료:", fixed_filename)

                os.remove(zip_filepath)
                print("  - ZIP 삭제 완료:", zip_filename)
            else:
                print("  × 다운로드 실패:", response_download.status_code)

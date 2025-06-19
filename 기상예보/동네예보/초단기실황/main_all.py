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

korean_labels = ["강수형태", "습도", "강수", "하늘상태", "기온", "뇌전", "풍향", "풍속"]


var_codes = [
    "PTY",
    "REH",
    "RN1",
    "SKY",
    "T1H",
    "LGT",
    "VEC",
    "WSD",
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
        "Referer": "ttps://data.kma.go.kr/data/rmt/rmtList.do?code=410&pgmNo=571",
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
        "Referer": "ttps://data.kma.go.kr/data/rmt/rmtList.do?code=410&pgmNo=571",
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
def generate_month_intervals(start_date: datetime, end_date: datetime):
    """
    start_date부터 end_date까지 매월의 'YYYYMM' 문자열을 리스트로 반환합니다.
    ex) ['201007', '201008', ..., '202504']
    """
    intervals = []
    current = start_date.replace(day=1)
    # end_date의 해당 월까지 포함시키려면 month 단위로 <= 비교
    while current <= end_date:
        intervals.append(current.strftime("%Y%m"))
        current += relativedelta(months=1)
    return intervals


# -------------------------------
# 요청 본문 생성 함수
# -------------------------------
def generate_first_request_body(
    column: tuple, start: str, end: str, stnm: str, 동코드
) -> dict:
    data_code = "400"  # 동네예보 코드
    return {
        "apiCd": "request400",
        "data_code": data_code,
        "hour": "",
        "pageIndex": "1",
        "from": start,
        "to": end,
        "file_size": "",
        "reqst_purpose_cd": "F00401",
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


def load_region_code(source_path: str) -> pd.DataFrame:
    df = pd.read_csv(source_path)
    df["지역키"] = df["Level1"] + "|" + df["Level2"] + "|" + df["Level3"]
    return df


def get_region_slice(df: pd.DataFrame, method: str, value: str) -> pd.DataFrame:
    if method == "from_region":
        start_idx = df[df["지역키"] == value].index[0]
        return df.iloc[start_idx:].copy()
    elif method == "exact_match":
        return df[df["지역키"] == value].copy()
    elif method == "starts_with":
        return df[df["지역키"].str.startswith(value)].copy()
    elif method == "custom_range":
        start, end = value.split(",")
        return df.iloc[int(start) : int(end)].copy()
    else:
        raise ValueError(f"지원하지 않는 필터링 방식입니다: {method}")


def get_cookie():
    login_url = "https://data.kma.go.kr/login/loginAjax.do"
    session = requests.Session()
    response = session.post(
        login_url,
        data={
            "loginId": "shdbtjd8@gmail.com",  # 여기에 KMA 계정 ID 입력
            "passwordNo": "yuseong0745%",  # 여기에 KMA 계정 비밀번호 입력
        },
    )
    if response.status_code == 200:
        cookies = session.cookies.get_dict()
        cookie_str = "; ".join([f"{key}={value}" for key, value in cookies.items()])
        return cookie_str
    else:
        raise Exception("Failed to retrieve cookies from KMA login page.")


def get_headers(cookie_str: str) -> dict:
    return create_first_header(cookie_str), create_second_header(cookie_str)


# -------------------------------
# 경로 및 데이터 준비
# -------------------------------

# BASE_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# 지역코드_파일경로 = os.path.join(BASE_SCRIPT_DIR, "지역코드_sep.csv")

# 지역코드_df = load_region_code(지역코드_파일경로)
# filtered_df = get_region_slice(
#     지역코드_df,
#     method="from_region",  # 또는 "starts_with", "exact_match", "custom_range"
#     value="서울특별시|종로구|교남동",  # 또는 인덱스 범위 등
# )
# filtered_df = 지역코드_df
# 동_set = filtered_df[["Level1", "Level2", "Level3", "ReqList_Last"]].values.tolist()

동_set = [("부산광역시", "동구", "초량제3동", "97_74")]


BASE_DIR = os.path.join("data", "기상예보", "동네예보", "초단기실황")
# 날짜 생성
start_date_obj = datetime(2010, 7, 1)
end_date_obj = datetime(2025, 4, 30)
month_intervals = generate_month_intervals(start_date_obj, end_date_obj)


# -------------------------------
# 실행
# -------------------------------
cookie_str = get_cookie()
print("쿠키 정보:", cookie_str)
first_header, second_header = get_headers(cookie_str)

import time

time.sleep(1)

for level1, level2, level3, 동코드 in 동_set:
    dong_dir = os.path.join(BASE_DIR, level1, level2, level3)
    os.makedirs(dong_dir, exist_ok=True)

    for ym in month_intervals:
        start = ym
        end = ym
        for column in COLUMN_SET:
            request_body = generate_first_request_body(
                column, start, end, level3, 동코드
            )

            url_generation = (
                "https://data.kma.go.kr/mypage/rmt/callDtaReqstIrods4xxAjax.do"
            )
            print(f"[{level3}] 요청 중: {column[0]} | {start} ~ {end}")
            session.post(url_generation, headers=first_header, data=request_body)

            url_download = "https://data.kma.go.kr/data/rmt/downloadZip.do"
            data_download = {
                "downFile": generate_second_request_body(level3, column[0], start, end)
            }
            response_download = session.post(
                url_download, headers=second_header, data=data_download, stream=True
            )

            if response_download.status_code == 200:
                zip_filename = f"{level3}_{column[0]}_{start}_{end}.zip"
                zip_filepath = os.path.join(dong_dir, zip_filename)
                with open(zip_filepath, "wb") as f:
                    for chunk in response_download.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                print("  - 다운로드 완료:", zip_filename)

                category_dir = os.path.join(dong_dir, column[0])
                os.makedirs(category_dir, exist_ok=True)
                is_downloaded = False
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
                        is_downloaded = True

                if not is_downloaded:
                    print("  × ZIP 파일에서 추출된 파일이 없습니다.")
                    cookie_str = get_cookie()
                    first_header, second_header = get_headers(cookie_str)

                os.remove(zip_filepath)
                print("  - ZIP 삭제 완료:", zip_filename)
            else:
                print("  × 다운로드 실패:", response_download.status_code)

import os
import csv
import json
import time
import urllib.parse
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


def get_login_cookie(driver):
    """
    https://data.kma.go.kr/cmmn/main.do 에 접속하여 로그인 버튼 클릭,
    모달창에 이메일과 비밀번호를 입력 후 로그인 요청하고, 쿠키에서 JSESSIONID를 추출합니다.
    """
    driver.get("https://data.kma.go.kr/cmmn/main.do")
    driver.find_element(By.CSS_SELECTOR, "#loginBtn").click()
    time.sleep(2)

    email = "shdbtjd8@gmail.com"  # 본인 이메일로 변경
    password = "yuseong0745%"  # 본인 비밀번호로 변경

    driver.find_element(By.CSS_SELECTOR, "#loginId").send_keys(email)
    driver.find_element(By.CSS_SELECTOR, "#passwordNo").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "#loginbtn").click()
    time.sleep(5)  # 로그인Ajax 요청 및 로그인 완료 대기

    cookies = driver.get_cookies()
    jsession = ""
    for cookie in cookies:
        if cookie["name"] == "JSESSIONID":
            jsession = cookie["value"]
    login_cookie = f"loginId={email}; JSESSIONID={jsession}"
    return login_cookie


def process_request_body(request_body: str, csv_file: str = "request_log.csv"):
    """
    URL 인코딩된 요청 본문을 파싱하여 딕셔너리로 만들고,
    CSV 파일에 한 행으로 저장합니다.

    - 동일 key가 여러 번 있으면 쉼표로 구분하여 합칩니다.
    - CSV 파일이 없으면 생성하고, 이미 있으면 새로운 컬럼이 있으면 추가합니다.
    """
    # URL 인코딩된 문자열 파싱 (parse_qs는 value를 list로 반환)
    parsed = urllib.parse.parse_qs(request_body)
    # 같은 key가 여러 번 있을 경우, 리스트의 값들을 쉼표로 합치기
    row = {k: ",".join(v) for k, v in parsed.items()}

    # 기존 CSV 파일 읽기 (존재하면)
    if os.path.exists(csv_file):
        try:
            df = pd.read_csv(csv_file, dtype=str)
        except Exception as e:
            print("CSV 파일 읽기 에러:", e)
            df = pd.DataFrame()
    else:
        df = pd.DataFrame()

    # 기존 헤더와 row의 키들을 모두 포함하는 컬럼 목록 생성
    all_columns = list(set(df.columns).union(set(row.keys())))

    # 기존 DataFrame에 누락된 컬럼이 있으면 빈 문자열로 채움
    for col in all_columns:
        if col not in df.columns:
            df[col] = ""

    # row 데이터도 all_columns 순서에 맞춰 정리 (없는 키는 빈 문자열)
    new_row = {col: row.get(col, "") for col in all_columns}

    # DataFrame에 새로운 행 추가 (append() 대신 pd.concat() 사용)
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    # 컬럼 순서를 정리하여 CSV로 저장 (utf-8-sig: 한글 인코딩 문제 해결)
    df = df[all_columns]
    df.to_csv(csv_file, index=False, encoding="utf-8-sig")
    print(f"요청 데이터가 {csv_file} 파일에 저장되었습니다.")


def capture_requests(driver):
    """
    Selenium의 performance 로그에서 'callDtaReqstIrods4xxNewAjax.do' 요청의 request body를 캡처하여 CSV에 저장합니다.
    """
    logs = driver.get_log("performance")
    for entry in logs:
        try:
            message = json.loads(entry["message"])["message"]
        except Exception:
            continue
        # Network.requestWillBeSent 이벤트 필터링
        if message.get("method") == "Network.requestWillBeSent":
            request = message.get("params", {}).get("request", {})
            url = request.get("url", "")
            if "callDtaReqstIrods4xxNewAjax.do" in url:
                postData = request.get("postData")
                if postData:
                    print("캡처된 요청 URL:", url)
                    print("요청 본문:", postData)
                    print("-" * 80)
                    # CSV 파일에 저장
                    process_request_body(postData)


# --- ChromeDriver 및 Performance 로그 설정 ---
chrome_options = Options()
chrome_options.add_experimental_option("perfLoggingPrefs", {"enableNetwork": True})
chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

driver = webdriver.Chrome(options=chrome_options)

# --- 로그인 수행 및 쿠키 추출 ---
login_cookie = get_login_cookie(driver)
print("로그인 쿠키:", login_cookie)

# --- 대상 페이지로 이동 ---
driver.get("https://data.kma.go.kr/data/rmt/rmtList.do?code=420&pgmNo=574")
time.sleep(3)

# --- 버튼 클릭 시퀀스 실행 ---
page_num = 3
# 1. #ztree_1_check 버튼 2회 클릭
for _ in range(2):
    try:
        driver.find_element(By.CSS_SELECTOR, "#ztree_1_check").click()
        time.sleep(1)
    except Exception as e:
        print("ztree_1_check 클릭 실패:", e)

# 2. "#dsForm > div.wrap_btn > button" 클릭
try:
    driver.find_element(By.CSS_SELECTOR, "#dsForm > div.wrap_btn > button").click()
except Exception as e:
    print("dsForm 버튼 클릭 실패:", e)
time.sleep(10)  # 요청 준비 시간

# --- 페이지 반복 작업 시작 ---

for i in range(page_num - 1):
    try:
        next_btn = driver.find_element(
            By.CSS_SELECTOR,
            "#wrap_content > div.wrap_itm.area_data > div.cont_itm > div.ft_lst > div.wrap_paging > ul > li.next > a",
        )
        next_btn.click()
        page_num += 1
        time.sleep(5)  # 다음 페이지 로딩 대기
    except Exception as e:
        print("다음 페이지 버튼을 찾을 수 없으므로 작업을 종료합니다.", e)
        break

while True:
    print(f"\n===== 페이지 {page_num} 작업 시작 =====")

    # 3. "#checkAll" 버튼 클릭
    try:
        driver.find_element(By.CSS_SELECTOR, "#checkAll").click()
    except Exception as e:
        print("checkAll 버튼 클릭 실패:", e)
    time.sleep(1)

    # 4. "#wrap_content > div.wrap_itm.area_data > div.cont_itm > div.ft_lst > div.right > a" 클릭
    try:
        driver.find_element(
            By.CSS_SELECTOR,
            "#wrap_content > div.wrap_itm.area_data > div.cont_itm > div.ft_lst > div.right > a",
        ).click()
    except Exception as e:
        print("데이터 요청 버튼 클릭 실패:", e)
    time.sleep(2)

    # 5. 만약 "#reqstPurposeCd14" 요소가 있으면 클릭 후 요청 버튼 클릭
    try:
        req_elem = driver.find_element(By.CSS_SELECTOR, "#reqstPurposeCd14")
        req_elem.click()
        time.sleep(1)
        driver.find_element(
            By.CSS_SELECTOR,
            "#sltUsePop > div > div > div.cont_layer.box > div > a.btn_request",
        ).click()
        time.sleep(2)
    except Exception as e:
        print("#reqstPurposeCd14 요소가 없으므로 해당 단계 건너뜁니다.")

    # 6. 요청 전송 후 충분한 시간 대기 (네트워크 요청이 모두 발생하도록)
    time.sleep(120)

    # --- 해당 페이지의 요청 캡처 및 CSV 저장 ---
    capture_requests(driver)

    # --- 다음 페이지로 이동 ---
    try:
        next_btn = driver.find_element(
            By.CSS_SELECTOR,
            "#wrap_content > div.wrap_itm.area_data > div.cont_itm > div.ft_lst > div.wrap_paging > ul > li.next > a",
        )
        next_btn.click()
        page_num += 1
        time.sleep(5)  # 다음 페이지 로딩 대기
    except Exception as e:
        print("다음 페이지 버튼을 찾을 수 없으므로 작업을 종료합니다.", e)
        break

driver.quit()

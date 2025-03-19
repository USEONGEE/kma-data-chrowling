import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


def get_login_cookie(driver):
    """
    https://data.kma.go.kr/cmmn/main.do 에 접속하여 로그인 버튼 클릭,
    모달창에 이메일과 비밀번호를 입력 후 로그인 요청하고, 쿠키에서 JSESSIONID를 추출합니다.
    """
    driver.get("https://data.kma.go.kr/cmmn/main.do")
    # 로그인 버튼(#loginBtn) 클릭
    driver.find_element(By.CSS_SELECTOR, "#loginBtn").click()
    time.sleep(2)

    email = "shdbtjd8@gmail.com"  # 본인 이메일로 변경
    password = "yuseong0745%"  # 본인 비밀번호로 변경

    # 모달 내 로그인 폼에 이메일과 비밀번호 입력
    driver.find_element(By.CSS_SELECTOR, "#loginId").send_keys(email)
    driver.find_element(By.CSS_SELECTOR, "#passwordNo").send_keys(password)

    # 로그인 버튼(#loginbtn) 클릭
    driver.find_element(By.CSS_SELECTOR, "#loginbtn").click()
    time.sleep(5)  # 로그인Ajax 요청 및 로그인 완료 대기

    # 쿠키에서 JSESSIONID 추출
    cookies = driver.get_cookies()
    jsession = ""
    for cookie in cookies:
        if cookie["name"] == "JSESSIONID":
            jsession = cookie["value"]
    login_cookie = f"loginId={email}; JSESSIONID={jsession}"
    return login_cookie


# --- ChromeDriver 및 Performance 로그 설정 ---
chrome_options = Options()
# performance 로그 활성화 (네트워크 캡처를 위해)
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
# 1. #ztree_1_check 버튼을 2번 클릭
for _ in range(2):
    driver.find_element(By.CSS_SELECTOR, "#ztree_1_check").click()
    time.sleep(1)

# 2. "#dsForm > div.wrap_btn > button" 클릭
driver.find_element(By.CSS_SELECTOR, "#dsForm > div.wrap_btn > button").click()
time.sleep(10)  # 요청을 위한 준비 시간

# 3. "#checkAll" 버튼 클릭
driver.find_element(By.CSS_SELECTOR, "#checkAll").click()
time.sleep(1)

# 4. "#wrap_content > div.wrap_itm.area_data > div.cont_itm > div.ft_lst > div.right > a" 버튼 클릭
driver.find_element(
    By.CSS_SELECTOR,
    "#wrap_content > div.wrap_itm.area_data > div.cont_itm > div.ft_lst > div.right > a",
).click()
time.sleep(2)

# 5. 만약 화면에 "#reqstPurposeCd14" 요소가 있다면 클릭 후, 요청 버튼 클릭
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
    print("#reqstPurposeCd14 요소가 없으므로 해당 단계는 건너뜁니다.")

# --- 여기부터 요청들이 전송되기 시작 ---
# 충분한 시간 대기하여 네트워크 요청이 모두 발생하도록 함
time.sleep(60)

# --- performance 로그에서 "callDtaReqstIrods4xxNewAjax.do" 요청의 request body 캡처 ---
logs = driver.get_log("performance")
print("\n----- 캡처된 'callDtaReqstIrods4xxNewAjax.do' 요청들 -----")
for entry in logs:
    try:
        message = json.loads(entry["message"])["message"]
    except Exception as e:
        continue
    # "Network.requestWillBeSent" 이벤트 필터링
    if message.get("method") == "Network.requestWillBeSent":
        request = message.get("params", {}).get("request", {})
        url = request.get("url", "")
        if "callDtaReqstIrods4xxNewAjax.do" in url:
            print("요청 URL:", url)
            print("요청 방식:", request.get("method"))
            postData = request.get("postData")
            print("요청 본문:", postData)
            print("------------------------------------------------------")

driver.quit()

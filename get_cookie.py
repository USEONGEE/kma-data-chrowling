import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# 크롬 옵션 설정: performance 로그 활성화
chrome_options = Options()
chrome_options.add_experimental_option("perfLoggingPrefs", {"enableNetwork": True})
chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

# ChromeDriver 실행 (chromedriver가 PATH에 있어야 합니다)
driver = webdriver.Chrome(options=chrome_options)


# 대상 페이지로 이동
def get_login_cookie(driver):
    driver.get("https://data.kma.go.kr/cmmn/main.do")

    # 로그인 버튼(#loginBtn) 클릭
    login_btn = driver.find_element(By.CSS_SELECTOR, "#loginBtn")
    login_btn.click()

    # 모달창이 뜰 때까지 잠시 대기
    time.sleep(2)

    email = "shdbtjd8@gmail.com"

    # 모달창 내 로그인 폼에 이메일 입력 (#loginId)
    login_id_input = driver.find_element(By.CSS_SELECTOR, "#loginId")
    login_id_input.send_keys(email)  # 본인의 이메일로 변경

    # 비밀번호 입력 (#passwordNo)
    password_input = driver.find_element(By.CSS_SELECTOR, "#passwordNo")
    password_input.send_keys("yuseong0745%")  # 본인의 비밀번호로 변경

    # 로그인 버튼 클릭 (#loginbtn)
    login_submit = driver.find_element(By.CSS_SELECTOR, "#loginbtn")
    login_submit.click()

    # 로그인Ajax 요청이 발생할 시간을 주기 위해 대기
    time.sleep(5)

    cookies = driver.get_cookies()
    for cookie in cookies:
        if cookie["name"] == "JSESSIONID":
            cookie = cookie["value"]

    return f"loginId={email}; JSESSIONID={cookie}"

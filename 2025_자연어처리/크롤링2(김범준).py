# 크롤링을 위한 셀레니움
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 크롤링을 위한 requests와 beautifulsoup
import requests
import certifi
from bs4 import BeautifulSoup

# 데이터 프레임 작성을 위한 판다스
import pandas as pd

# 한국어만 추출출
import re

# 대기시간을 휘한 라이브러리
import random
import time
from tqdm import tqdm

# 폴더 생성
import os

def croll():
    for i in tqdm(range(1, 102)):
        if i == 6:
            continue
        try:
            driver.find_element(By.XPATH, f'/html/body/main/article[2]/section/section[2]/section[2]/article[{i}]/section[1]/section[2]/article/a').click()
            #/html/body/main/article[2]/section/section[2]/section[2]/article[6]
            #/html/body/main/article[2]/section/section[2]/section[2]/article[5]/section[1]/section[2]/article/a
        except:
            break
        
        driver.switch_to.window(driver.window_handles[-1])
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '#thesisTitle')))
        soup = BeautifulSoup(driver.page_source, features="html.parser")
        title = soup.select_one("h1.thesisDetail__tit").text.strip()
        year_li = soup.find_all("li", "journalList__item")
        year = year_li[3].find("span").text

        # 주제어 수집
        keywords_list = []
        keyword_elem = soup.find_all("a", class_="keywordWrap__keyword")
        if keyword_elem:
            for keyword in keyword_elem:
                keywords_list.append(keyword.text.replace("#", "").strip())
        else:
            keywords_list = None

        # 초록 내용 수집
        abstract_elem = soup.select_one("div.abstractTxt")
        if abstract_elem:
            abstract_text = abstract_elem.text.strip()
            abstract_parts = abstract_text.split('  ')
            if len(abstract_parts) > 1:
                abstract = abstract_parts[0].strip()
                multilingual_abstract = abstract_parts[1].strip()
            else:
                pattern = re.compile('[^ㄱ-ㅎ가-힣]+')
                result = re.sub(pattern, '', abstract_parts[0])
                if len(result) < 10:
                    abstract = None
                    multilingual_abstract = abstract_parts[0].strip()
                else:
                    abstract = abstract_parts[0].strip()
                    multilingual_abstract = None
                #abstract = abstract_parts[0].strip() if len(abstract_parts) > 0 else ""
                #multilingual_abstract = abstract_parts[1].strip() if len(abstract_parts) > 1 else ""
        else:
            abstract = None
            multilingual_abstract = None

        # 데이터를 리스트에 저장
        titles.append(title)
        date.append(year)
        keywords.append(keywords_list)
        abstracts.append(abstract)
        multilingual_abstracts.append(multilingual_abstract)

        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        time.sleep(1)

# 논문 검색 설정
search = input('검색할 키워드 : ')
min_year = input('추출할 최소 년도를 입력 : ')
max_year = input('추출할 최대 년도를 입력 : ')
time.sleep(1)

driver = webdriver.Chrome()
driver.get('https://www.dbpia.co.kr/')
driver.implicitly_wait(10)

# 설정한 키워드로 검색
driver.find_element(By.XPATH, '//*[@id="searchInput"]').click()
time.sleep(0.5)
driver.find_element(By.XPATH, '//*[@id="searchInput"]').send_keys(search)
time.sleep(0.2)
driver.find_element(By.XPATH, '//*[@id="submitSearchInput"]').click()
time.sleep(3)

# kci 논문 보기 설정
driver.find_element(By.CSS_SELECTOR, '#domesticRecord_064001').click()
##domesticRecord_064001
time.sleep(1)
driver.find_element(By.CSS_SELECTOR, '#domesticRecord_064005').click()
# #domesticRecord_064005
time.sleep(1)
driver.find_element(By.CSS_SELECTOR, '#domesticRecord_064002').click()
#domesticRecord_064002
time.sleep(2)

# 페이지를 불러올 년도 설정
driver.find_element(By.XPATH, '//*[@id="yearRangeMin"]').click()
driver.find_element(By.XPATH, '//*[@id="yearRangeMin"]').send_keys(min_year)
time.sleep(0.3)
driver.find_element(By.XPATH, '//*[@id="yearRangeMax"]').click()
driver.find_element(By.XPATH, '//*[@id="yearRangeMax"]').send_keys(max_year)
time.sleep(0.3)
driver.find_element(By.XPATH, '//*[@id="yearRangeSearch"]').click()
time.sleep(3)

# 페이지를 100개씩 보기로 설정
driver.find_element(By.XPATH, '//*[@id="selectTitle"]').click()
driver.find_element(By.XPATH, '//*[@id="get100PerPage"]').click()
time.sleep(3)

# 페이지 수 게산
article_num = driver.find_element(By.XPATH, '//*[@id="totalCount"]').text
article_num = int(article_num[:-1].replace(',',''))
page_num = article_num // 100 + 1
print('추출할 논문의 수 : ', article_num)

# 저장할 데이터 초기화
titles = []
date = []
keywords = []
abstracts = []
multilingual_abstracts = []

for x in tqdm(range(1,page_num+1)):
    try:
        if x == 1:
            croll()
            continue
        if x % 10 == 1:
            driver.find_element(By.XPATH, '//*[@id="goNextPage"]').click()
        else:
            if x % 10 ==0:
                driver.find_element(By.XPATH, '//*[@id="pageList"]/a[10]').click()
            else:
                driver.find_element(By.XPATH, f'//*[@id="pageList"]/a[{x%10}]').click()
        time.sleep(3)
        if x % 5 == 0:
            time.sleep(random.randint(3, 5))
        croll()
    except:
        break

# 데이터 프레임 생성
data = pd.DataFrame({
    'title': titles,
    'year': date,
    'keywords': keywords,
    'abstract': abstracts,
    'multilingual_abstract': multilingual_abstracts
})

safe_search = search.replace(" ", "_")
# 검색어를 포함한 파일명 생성
csv_filename = f"{safe_search}_{min_year}_dbpia.csv"

# 폴더 경로 설정
dbpia_folder = "dbpia"

# 폴더 생성 (존재하지 않으면 생성)
os.makedirs(dbpia_folder, exist_ok=True)

# 데이터 프레임을 csv 형태로 저장
csv_file_path = f"{dbpia_folder}/{csv_filename}"
data.to_csv(csv_file_path, index=False)

driver.close()

print('추출한 논문의 수 : ', len(titles))
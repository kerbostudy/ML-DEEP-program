import time  # 시간 관련 기능을 제공하는 라이브러리
import pandas as pd  # 데이터 분석 및 처리를 위한 라이브러리 (데이터프레임 사용)
from selenium import webdriver  # 웹 브라우저 자동화를 위한 라이브러리
from selenium.webdriver.common.by import By  # HTML 요소 검색 방식을 지정하는 클래스 (ID, CSS 선택자 등)
from selenium.webdriver.support.ui import WebDriverWait  # 웹 페이지 요소 로딩을 기다리는 클래스
from selenium.webdriver.support import expected_conditions as EC  # WebDriverWait와 함께 사용되는 조건 클래스 (요소 존재 여부 등)
from bs4 import BeautifulSoup  # HTML 및 XML 문서를 파싱하는 라이브러리

# URL 생성 함수
def generate_page_url(keyword):
    """검색 키워드를 사용하여 DBpia 검색 페이지 URL을 생성합니다."""
    return f"https://www.dbpia.co.kr/search/topSearch?searchOption=all&query={keyword}"

# 브라우저 드라이버 실행
driver = webdriver.Chrome()

try:
    # 키워드 설정
    search_keyword = "딥러닝"  # 검색 키워드
    max_pages = 210  # 순회할 페이지 수

    # URL 생성 및 이동
    url = generate_page_url(search_keyword)
    driver.get(url)

    # 체크박스 ID 목록 (미등재 제외)
    checkbox_ids = [
        "domesticRecord_064001",  # KCI등재
        "domesticRecord_064005",  # KCI우수등재
        "domesticRecord_064002"   # KCI등재후보
    ]

    # 체크박스 선택
    for checkbox_id in checkbox_ids:
        try:
            checkbox = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, checkbox_id))
            )
            if not checkbox.is_selected():
                driver.execute_script("arguments[0].click();", checkbox)
        except Exception as e:
            print(f"체크박스 {checkbox_id} 처리 중 오류 발생: {e}")

    # 4초 대기
    time.sleep(4)

    # 논문 데이터를 저장할 리스트
    papers = []
    detail_page_links = []

    # 페이지 순회
    for current_page in range(1, max_pages + 1):
        print(f"[페이지 {current_page}] 데이터를 처리 중입니다...")

        # 로딩 대기 및 페이지 소스 파싱
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#searchResultList > article:nth-child(1)"))
        )
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # 논문 데이터 추출
        for n in range(1, 22):  # 1~21번째 논문
            article_selector = f"#searchResultList > article:nth-child({n})"
            article = soup.select_one(article_selector)
            if not article:
                continue

            # 상세페이지 링크 추출
            link_tag = article.find("a", class_="thesis__link title")
            if link_tag and link_tag.has_attr('href'):
                detail_page_url = link_tag['href']
                full_detail_page_url = f"https://www.dbpia.co.kr{detail_page_url}" if detail_page_url.startswith("/") else detail_page_url
            else:
                full_detail_page_url = None

            # 제목 추출
            title_tag = link_tag.find("h2", class_="thesis__tit") if link_tag else None
            title = title_tag.get_text(strip=True) if title_tag else "제목 없음"

            # 초록 추출
            abstract_span = article.find("span", class_="thesis__abstract")
            abstract = abstract_span.get_text(strip=True) if abstract_span else None

            # 저자 추출
            authors = [author.get_text(strip=True) for author in article.select("span.thesis__author")]

            # 키워드 추출
            keywords_section = article.find("section", class_="thesis__keyword")
            keywords = [keyword.get_text(strip=True) for keyword in keywords_section.find_all("i")] if keywords_section else []

            # 날짜 추출
            date_span = article.select_one("section.thesisWrap__left > section.thesisWrap__bottomWrap > article > section.thesisAdditionalInfo.thesis__info > span:nth-child(5)")
            date = date_span.get_text(strip=True) if date_span else "날짜 없음"

            # 상세페이지 링크 저장
            if not abstract and full_detail_page_url:
                detail_page_links.append((title, full_detail_page_url))

            # 데이터 저장 (제목, 초록, 저자, 키워드, 날짜 중 하나라도 존재할 경우)
            papers.append({
                "제목": title if title else "제목 없음",
                "초록": abstract if abstract else "초록 없음",
                "저자": ", ".join(authors) if authors else "저자 정보 없음",
                "키워드": ", ".join(keywords) if keywords else "키워드 없음",
                "날짜": date,
                "상세페이지": full_detail_page_url
            })

        # 다음 페이지로 이동
        if current_page % 10 == 0:
            try:
                next_button = driver.find_element(By.ID, "goNextPage")
                next_button.click()
                time.sleep(4)
            except Exception as e:
                print(f"다음 페이지 버튼 클릭 오류: {e}")
                break
        else:
            try:
                next_page_selector = f"a.dpPaging__link[onclick='setPageNum({current_page + 1})']"
                next_page_element = driver.find_element(By.CSS_SELECTOR, next_page_selector)
                next_page_element.click()
                time.sleep(4)
            except Exception as e:
                print(f"다음 페이지 이동 중 오류 발생: {e}")
                break

    # 상세페이지 초록 데이터 추가 처리
    for title, detail_url in detail_page_links:
        try:
            driver.get(detail_url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#dpMain > section > section.thesisDetail__abstract > div.abstractTxt"))
            )
            detail_soup = BeautifulSoup(driver.page_source, 'html.parser')
            abstract_tag = detail_soup.select_one("#dpMain > section > section.thesisDetail__abstract > div.abstractTxt")
            abstract = abstract_tag.get_text(strip=True) if abstract_tag else "초록 없음"

            # 논문 데이터 업데이트
            for paper in papers:
                if paper["제목"] == title:
                    paper["초록"] = abstract
                    break

        except Exception as e:
            print(f"상세페이지 {detail_url} 처리 중 오류 발생: {e}")

    # 데이터프레임 생성
    df = pd.DataFrame(papers)

    # 제목, 초록, 저자가 모두 없는 데이터 제거
    df = df[~((df["제목"] == "제목 없음") & (df["초록"] == "초록 없음") & (df["저자"] == "저자 정보 없음"))]

    # 데이터프레임 저장
    file_name = f"dbpia_papers_{search_keyword}_pages_{max_pages}.csv"
    df.to_csv(file_name, index=False, encoding="utf-8-sig")
    print(f"데이터가 {file_name}에 저장되었습니다.")

finally:
    # 브라우저 종료
    driver.quit()
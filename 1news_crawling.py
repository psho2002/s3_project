from numpy import NaN
from selenium import webdriver
from bs4 import BeautifulSoup
from urllib.parse import quote
import urllib.request
import pandas as pd
import time

def get_news(query, start_date, end_date, page_num=10):

    news_df = pd.DataFrame(columns=("Title","Link","Press","Datetime", "Article", "Good", "Warm", "Sad", "Angry", "Want", "Recommand", "Reply"))
    idx = 0

    url_query = quote(query)
    start_date = quote(start_date)
    end_date = quote(end_date)



    url = 'https://search.naver.com/search.naver?&where=news&sm=nws_hty&query='+url_query+"&docid=&nso=so%3Ar%2Cp%3Afrom"+start_date+"to"+end_date

    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    driver = webdriver.Chrome(options=options)

    #첫 페이지 로딩시 시간이 많이 걸리니 미리 띄워서 대기시간을 많이 넣어준다.
    search_url = urllib.request.urlopen(url).read()
    soup =BeautifulSoup(search_url, 'html.parser')
    links = soup.find_all('div', {'class':'info_group'})
    first_url = links[0].find_all('a', {'class':'info'})[-1].get('href')
    driver.get(first_url)
    time.sleep(0.5)
    
    for _ in range(0, page_num):

        search_url = urllib.request.urlopen(url).read()
        soup =BeautifulSoup(search_url, 'html.parser')
        links = soup.find_all('div', {'class':'info_group'})

        for link in links:
            press = link.find_all('a', {'class':'info press'})[0].get('href')
            news_url = link.find_all('a', {'class':'info'})[-1].get('href')

            if 'news.naver' in news_url:
                news_link = urllib.request.urlopen(news_url).read()
                news_html = BeautifulSoup(news_link, 'html.parser')
                driver.get(news_url) #페이지를 미리 띄운 뒤 우선 request를 통한 크롤링부터 시행하고 나머지 동적페이지의 내용을 크롤링한다.


                while True:
                    try:
                        title = news_html.find('h3', {'id':'articleTitle'}).get_text()
                        datetime = news_html.find('span', {'class':'t11'}).get_text()
                        article = news_html.find('div', {'id':'articleBodyContents'}).get_text()
                        article = article.replace("\n", "")
                        article = article.replace("\t", "")
                        break
                    except :
                        title = NaN
                        datetime = NaN
                        article = NaN
                        link = NaN
                        break

                #감정 및 댓글등은 동적페이지라서 웹드라이버로 해야한다.
                
                time.sleep(0.2)#크롬 페이지 띄우는 시간동안 대기

                while True:#감정평가시스템 유무에 따른 처리
                    try:
                        good = driver.find_element_by_xpath('//*[@id="spiLayer"]/div[1]/ul/li[1]/a/span[2]').text
                        warm = driver.find_element_by_xpath('//*[@id="spiLayer"]/div[1]/ul/li[2]/a/span[2]').text
                        sad = driver.find_element_by_xpath('//*[@id="spiLayer"]/div[1]/ul/li[3]/a/span[2]').text
                        angry = driver.find_element_by_xpath('//*[@id="spiLayer"]/div[1]/ul/li[4]/a/span[2]').text
                        want = driver.find_element_by_xpath('//*[@id="spiLayer"]/div[1]/ul/li[5]/a/span[2]').text
                        break
                    except :
                        good = NaN
                        warm = NaN
                        sad = NaN
                        angry = NaN
                        want = NaN
                        break

                while True:#기사추천시스템 유무에 따른 처리
                    try :
                        recommand = driver.find_element_by_xpath('//*[@id="main_content"]/div[1]/div[3]/div/div[3]/div[1]/div/a/span[3]').text
                        recommand = recommand.replace("공감", "0")
                        break
                    except :
                        recommand = NaN
                        break
               
                while True:#댓글시스템 유무에 따른 처리
                    try :
                        reply = driver.find_element_by_xpath('//*[@id="articleTitleCommentCount"]/span[2]').text
                        reply = reply.replace("댓글", "0")
                        break
                    except :
                        reply =NaN
                        break

                news_df.loc[idx] = [title, news_url, press, datetime, article, good, warm, sad, angry, want, recommand, reply]
                idx += 1
                
            else: #네이버 뉴스 연예, 스포츠란의 경우는 클래스를 따로 지정해주거나 제외시킨다.
                continue
        
        try: #다음 페이지 버튼 있는지 확인하고 없으면 루프 끝냄
            next = soup.find('a', {'class':'btn_next'}).get('href')
            url = "https://search.naver.com/search.naver" + next
            
        except:
            print("마지막 페이지입니다.")
            break

    news_df = news_df.drop_duplicates(['Link']) # 중복된 뉴스주소가 있으면 행 삭제
    news_df = news_df.dropna(subset=['Title']) # 기사제목을 못 가져온 행 삭제
    driver.quit()    
    return news_df.to_csv('naver_news.csv', index=False)

query = input('검색 질의: ')
start_date = input('시작날짜(YYYYMMDD): ')
end_date = input('마지막날짜(YYYYMMDD): ')
news_df = get_news(query, start_date, end_date, 50)
print(news_df)
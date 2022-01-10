import requests
from lxml import etree
import time
import os
import warnings
from selenium import webdriver

warnings.simplefilter("ignore", DeprecationWarning)


config = {
    "ACCOUNT": "YOUR ACCOUNT",
    "PASSWORD": "YOUR PASSWORD",
    "main_url": "https://www.qcc.com",
    "company_url": [
        "https://www.qcc.com/cassets/2e5f8bce7075d59edcaeb85fb5c3a33e.html",
        "https://www.qcc.com/cassets/5058554f24ff2d782958f317b60737df.html",
        "https://www.qcc.com/cassets/b72a27ba8c4bacd49bc5d77e244b6b4f.html",
        "https://www.qcc.com/cassets/99535d72f42b3c91d181921c2823b1ad.html"
    ]
}


def webdriver_engine():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36")
    driver = webdriver.Chrome(chrome_options=chrome_options, executable_path="chromedriver.exe")
    driver.maximize_window()
    return driver


def login_with_password(driver):
    driver.find_element_by_xpath("/html/body/div[3]/div/div/div/div[2]/div[1]/div[2]").click()  # 点击密码登录
    account_input = driver.find_element_by_xpath("/html/body/div[3]/div/div/div/div[2]/div[3]/form/div[1]/input")
    account_input.send_keys(config.get("ACCOUNT"))
    pass_input = driver.find_element_by_xpath("/html/body/div[3]/div/div/div/div[2]/div[3]/form/div[2]/input")
    pass_input.send_keys(config.get("PASSWORD"))
    time.sleep(1)
    driver.find_element_by_xpath("/html/body/div[3]/div/div/div/div[2]/div[3]/form/div[4]/button/strong").click()  # 点击登录


def login_with_captcha(driver):
    account_input = driver.find_element_by_xpath("/html/body/div[3]/div/div/div/div[2]/div[2]/form/div[1]/input")
    account_input.send_keys(config.get("ACCOUNT"))
    time.sleep(1)
    driver.find_element_by_xpath("/html/body/div[3]/div/div/div/div[2]/div[2]/form/div[3]/a").click()  # 点击发送验证码
    time.sleep(30)  # 输入验证码等待时长
    driver.find_element_by_xpath("/html/body/div[3]/div/div/div/div[2]/div[2]/form/div[4]/button").click()  # 点击登录


def login_in(driver, url, pwlogin=True):
    driver.get(url)
    time.sleep(2)
    driver.find_element_by_xpath("/html/body/div[1]/div[1]/div/div/nav[2]/ul/li[9]/a/span").click()  # 点击登录/注册
    time.sleep(3)
    if pwlogin:
        login_with_password(driver)   # 密码登录
    else:
        login_with_captcha(driver)      # 验证码登录
    time.sleep(2)
    print("login in success")

def int_and_max(data:list):
    result = []
    compare = 0
    for i in data:
        try:
            i = i.replace(".", "")
            result.append(int(i))
        except:
            continue
    for num in result:
        if num > compare:
            compare = num
    return compare


def request_company(driver, url):
    print(f"current company url: \n{url}")
    driver.get(url)
    time.sleep(2)
    whole_urls = []
    driver.find_element_by_xpath("/html/body/div[1]/div[2]/div[3]/div/div/div[1]/a[last()-2]/h2").click()  # 点击专利信息
    selector = etree.HTML(driver.page_source)
    company_name = selector.xpath("//*[@class='title']/div/span/h1[@class='copy-value']/text()")[0]
    page_num = selector.xpath("//*[@id='zhuanlilist']/div/div/nav/ul/li")
    if not page_num:
        raise Exception("没有专利信息！")
    page_list = []
    for num in page_num:
        page_list.append(num.xpath("a/text()")[0])
    max_page = int_and_max(page_list)
    patent_urls = selector.xpath("//*[@id='zhuanlilist']/div/div/table/tr/td[10]/span/a/@href")
    patent_urls = [config.get("main_url") + url for url in patent_urls if "http" not in url]
    whole_urls.extend(patent_urls)
    for page in range(1, max_page):
        try:
            if max_page <= 6:
                driver.find_element_by_xpath(f"//*[@id='zhuanlilist']/div/div[2]/nav/ul/li[last()]/a").click()
            if max_page == 7:
                driver.find_element_by_xpath(f"//*[@id='zhuanlilist']/div/div[2]/nav/ul/li[last()-1]/a").click()
            if max_page >= 8:
                if (max_page-page)<=3:
                    driver.find_element_by_xpath(f"//*[@id='zhuanlilist']/div/div[2]/nav/ul/li[last()-1]/a").click()
                else:
                    driver.find_element_by_xpath(f"//*[@id='zhuanlilist']/div/div[2]/nav/ul/li[last()-2]/a").click()
            time.sleep(2)
            selector = etree.HTML(driver.page_source)
            patent_urls = selector.xpath("//*[@id='zhuanlilist']/div/div/table/tr/td[10]/span/a/@href")
            patent_urls = [config.get("main_url") + url for url in patent_urls if "http" not in url]
            print(f"location page {page} now")
            whole_urls.extend(patent_urls)
        except Exception as err:
            print(f"no next page already, detail:{err}")
            continue
    print(f"专利数量: {len(whole_urls)}")
    print(">>>>start save patent files!<<<<")
    for patent_url in whole_urls:
        request_patent(driver, patent_url, company_name)


def request_patent(driver, url, company_name):
    driver.get(url)
    time.sleep(2)
    selector = etree.HTML(driver.page_source)
    pdf_url = selector.xpath("/html/body/div[1]/div[2]/section/a/@href")
    if len(pdf_url) > 0:
        pdf_url = pdf_url[0]
        name = selector.xpath("/html/body/div[1]/div[2]/section/div[1]/text()")[0]
        print(f"current pdf url:{pdf_url}")
        res = requests.get(pdf_url)
        pdf_back = pdf_url[pdf_url.rfind("/") + 1:]
        pdf_name = name + pdf_back
        pdf_name = pdf_name.replace("/", "-")
        print(f"save pdf file: {pdf_name}")
        if not os.path.exists(f"./patent_pdf/{company_name}"):
            os.mkdir(f"./patent_pdf/{company_name}")
        with open(f"./patent_pdf/{company_name}/" + pdf_name, "wb") as pdf:
            pdf.write(res.content)


def request_selenium():
    driver = webdriver_engine()
    login_in(driver, config.get("main_url"), pwlogin=True)
    for com_url in config.get("company_url"):
        try:
            request_company(driver, com_url)
        except Exception as err:
            print(f"something went wrong! detail: {err}")
            continue


if __name__ == '__main__':
    request_selenium()






import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import re
from datetime import datetime

# 设置配置变量
BASE_URL = 'http://jwxt.buaa.edu.cn:8080/ieas2.1'
LOGIN_URL = 'https://sso.buaa.edu.cn/login?service=' + quote(BASE_URL + '/welcome', 'utf-8')
USERNAME = ''
PASSWORD = ''
COURSE_TYPE = ''
COURSE_CODE = ''
SERIAL_CODE = '001'

TYPE_DICT = {
    '一般专业': ('xslbxk', 'ZYL', 'xslbxk'), 
    '核心专业': ('xslbxk', 'ZYL', 'xslbxk'), 
    '核心通识': ('xslbxk', 'TSL', 'tsk'), 
    '一般通识': ('xslbxk', 'TSL', 'qxrx'), 
    '体育': ('xslbxk', 'TSL', 'ty')
}
VAR1, VAR2, VAR3 = TYPE_DICT[COURSE_TYPE]

def get_current_term():
    now = datetime.now()
    year = now.year
    month = now.month

    if month >= 8:
        term = f"{year}-{year+1}-1"
        short_term = f"{year}{(year+1) % 100}1"
    elif month <= 1:
        term = f"{year-1}-{year}-1"
        short_term = f"{(year-1) % 100}{year % 100}1"
    else:
        term = f"{year-1}-{year}-2"
        short_term = f"{(year-1) % 100}{year % 100}2"

    return term, short_term

# 使用这个函数来设置RWH和pageXnxq
term, short_term = get_current_term()
RWH = f'{term}-{COURSE_CODE}-{SERIAL_CODE}'
PAGE_XNXQ = short_term

# 定义获取登陆令牌的函数
def get_login_token(session):
    r = session.get(LOGIN_URL)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, 'html.parser')
    return soup.find('input', {'name': 'execution'})['value']

# 定义登陆的函数
def login(session):
    formdata = {
        'username': USERNAME,
        'password': PASSWORD,
        'execution': get_login_token(session),
        'type': 'username_password',
        '_eventId': 'submit',
        'submit': '登陆'
    }
    r = session.post(LOGIN_URL, data=formdata, allow_redirects=True)
    soup = BeautifulSoup(r.text, "html.parser")
    return not soup.find_all('div', class_='error_txt')

# 定义提取隐藏项的函数
def get_hidden_items(text):
    item_pattern = re.compile(r'<input type="hidden" id=".*?" name="(.*?)"\s+value="(.*?)"')
    return {item.group(1): item.group(2) for item in item_pattern.finditer(text)}

# 定义提取消息的函数
def extract_message(html_text):
    message_pattern = re.compile(r"alert\('(.+?)'\);")
    match = message_pattern.search(html_text)
    return match.group(1) if match else None

# 定义选课的函数
def choose(session):
    list_url = f'{BASE_URL}/xslbxk/queryXsxkList?pageXkmkdm={VAR2}'
    response = session.post(list_url, allow_redirects=True)
    response.raise_for_status()

    payload = get_hidden_items(response.text)
    payload.update({
        'pageXnxq': PAGE_XNXQ,
        'pageXklb': VAR3,
        'pageYcctkc': '1',
        'rwh': RWH
    })
    
    response = session.post(f'{BASE_URL}/{VAR1}/saveXsxk', data=payload)
    message = extract_message(response.text)
    if message:
        print(message)
        if "选课成功" in message:
            exit()

# 主循环
def main():
    if (USERNAME == '' or 
        PASSWORD == '' or 
        COURSE_TYPE == '' or 
        COURSE_CODE == '' or 
        TEACHER_CODE == ''):
        
        print("请填写USERNAME, PASSWORD, COURSE_TYPE, COURSE_CODE 和 TEACHER_CODE的正确值。")
        exit()

    session = requests.Session()
    login(session)

    while True:
        choose(session)
        time.sleep(6)

if __name__ == "__main__":
    main()
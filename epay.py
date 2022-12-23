# epay SDK By Python
from config import API, ID, KEY, JUMP_URL
import requests
import hashlib
import json
import re
import sqlite3
import html5lib
from bs4 import BeautifulSoup
def make_data_dict(money, name, trade_id):
    data = {'pid': ID, 'sitename': 'Faka_Bot'}
    data.update(notify_url=JUMP_URL, return_url=JUMP_URL, money=money, name=name, out_trade_no=trade_id)
    return data


def epay_submit(order_data):
    items = order_data.items()
    items = sorted(items)
    p = items
    zhi1 = p[0]
    jine = zhi1[1]
    zhi2 = p[3]
    danh = zhi2[1]
    
    

    str = f'amount={jine}&notify_url=http://example.com/notify&order_id={danh}&redirect_url=http://example.com/redirect'


    hl = hashlib.md5()


    hl.update(str.encode(encoding='utf-8'))
    md5 = hl.hexdigest()

    print('MD5加密前为 ：' + str)
    print('MD5加密后为 ：' + hl.hexdigest())

    shujiaaa = {
        "order_id": f"{danh}",
        "amount": jine,
        "notify_url": "http://example.com/notify",
        "redirect_url": "http://example.com/redirect",
        "signature": f"{md5}"
    }
    headers = {'Content-Type': 'application/json'}
    x = requests.post('http://ep.cilol.xyz/api/v1/order/create-transaction', headers=headers, json=shujiaaa)
    print(x.text)
    s = json.dumps(x.json())

    s1 = json.loads(s)
    print(s1)
    s2 = (s1["data"])
    s3 = (s2["payment_url"])  
    # wg = f"{s3}"
   # db = sqlite3.connect("faka.sqlite3")
   # db.execute(f"UPDATE trade set wg = {s3} where uid={danh}")
   # db.commit()
    try:

        if s3 != 0:
            pay_url = s3
            return pay_url
    except Exception as e:
        print('submit | API请求失败')
        print(e)
        return 'API请求失败'
'''

    items = order_data.items()
    items = sorted(items)
    wait_sign_str = ''
    print(items)
    for i in items:
        wait_sign_str += str(i[0]) + '=' + str(i[1]) + '&'
    wait_for_sign_str = wait_sign_str[:-1] + KEY
    print(wait_for_sign_str)
    print(items)
    sign = hashlib.md5(wait_for_sign_str.encode('utf-8')).hexdigest()
    order_data.update(sign=sign, sign_type='MD5')
    print(sign)
    try:
        req = requests.post(API + 'submit.php', data=order_data)
        # print(req.text)
        content = re.search(r"<script>(.*)</script>", req.text).group(1)
        # print(content)
        if 'http' in content:
            pay_url = re.search(r"href=\'(.*)\'", content).group(1)
            return pay_url
        else:
            pay_url = API + re.search(r"\.\/(.*)\'", content).group(1)
            print(pay_url)
            trade_no = re.search(r'trade_no=(\d*)', content).group(1)
            print(trade_no)
            site_name = re.search(r"sitename=(.+?)'", content).group(1)
            print(site_name)
            return pay_url
    except Exception as e:
        print('submit | API请求失败')
        print(e)
        return 'API请求失败'
'''

def check_status(out_trade_no):
    s1 = out_trade_no
    print(out_trade_no)
    db = sqlite3.connect("faka.sqlite3")
    x = db.execute('select * from trade where trade_id=?', (f'{s1}',))
    values = x.fetchall()
    count_dict = dict()
    for item in values:
        if item in count_dict:
            count_dict[item] += 1
        else:
            count_dict[item] = 1

    wg = item[11]
    r = requests.get(wg)
    r.text
    soup = BeautifulSoup(r.text, 'html5lib') 
    jine = soup.find_all()[0].text 
    hhhh = "不存在待支付订单或已过期！"

    try:
        
        
        if jine == hhhh:
            print('支付成功')
            return '支付成功'
        else:
            print('支付失败')
            return '支付失败'
        
    except Exception as e:
        print('check_status | 请求失败')
        print(e)
        return 'API请求失败'
'''
    try:
        req = requests.get(API + 'api.php?act=order&pid={}&key={}&out_trade_no={}'.format(ID, KEY, out_trade_no), timeout=5)
        # print(req.text)
        rst = re.search(r"(\{.*?\})", req.text).group(1)
        # print(rst)
        rst_dict = json.loads(rst)
        # print(rst_dict)
        code = str(rst_dict['code'])
        if int(code) == 1:
            # trade_no = str(rst_dict['trade_no'])
            # msg = str(rst_dict['msg'])
            pay_status = str(rst_dict['status'])
            if pay_status == '1':
                print('支付成功')
                return '支付成功'
            else:
                print('支付失败')
                return '支付失败'
        else:
            print('查询失败，订单号不存在')
            return '查询失败，订单号不存在'
    except Exception as e:
        print('check_status | 请求失败')
        print(e)
        return 'API请求失败'
'''
'''
    s1 = pay_url
    s2 = out_trade_no
    print(s2)
    print(s1)

    try:
        req = requests.get(s1)
        # print(req.text)
        rst = re.search(r"(\{.*?\})", req.text).group(1)
        # print(rst)
        rst_dict = json.loads(rst)
        # print(rst_dict)
        code = str(rst_dict['code'])
        if int(code) == 1:
            # trade_no = str(rst_dict['trade_no'])
            # msg = str(rst_dict['msg'])
            pay_status = str(rst_dict['status'])
            if pay_status == '1':
                print('支付成功')
                return '支付成功'
            else:
                print('支付失败')
                return '支付失败'
        else:
            print('查询失败，订单号不存在')
            return '查询失败，订单号不存在'
    except Exception as e:
        print('check_status | 请求失败')
        print(e)
        return 'API请求失败'
'''
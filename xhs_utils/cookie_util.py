import json
import browser_cookie3

def write_cookie(host):
    # 获取chrome浏览器下的xiaohongshu的 cookie
    try:
        cookies = browser_cookie3.chrome(domain_name=host)
    except Exception as e:
        print(e)
        print("请关闭chrome或检查chrome版本是否过旧")
        return

    if cookies is None:
        print("没有获取到对应cookie")
        return

    cookie_dict = {}

    for cookie in cookies:
        cookie_dict[cookie.name] = cookie.value

    data = json.dumps(cookie_dict)
    # 把cookie写入cookies.txt文件中

    try:
        with open('./static/cookies.txt', 'w') as file:
            file.write(data)
        print("cookie写入成功")
    except Exception as e:
        print(e)
        print("cookie写入失败")

if __name__ == '__main__':
    write_cookie('xiaohongshu.com')

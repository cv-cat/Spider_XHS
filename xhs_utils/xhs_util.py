import os
import re
import sys
import time
import execjs
import requests
from pojo.note import Note_Detail
from pojo.user import User_Detail
from urllib.parse import urlparse
import imghdr
import tempfile

js = execjs.compile(open(r"./static/info.js", "r", encoding="utf-8").read())


def decodedUniChars(url):
    decodedUniChars = url.encode("utf-8").decode("unicode_escape")
    return decodedUniChars


def norm_str(str):
    new_str = re.sub(r"|[\\/:*?\"<>| ]+", "", str).replace("\n", "").replace("\r", "")
    return new_str


# 时间戳1681220903000 转YYYY-MM-DD HH:MM:SS
def timestamp_to_str(timestamp):
    time_local = time.localtime(timestamp / 1000)
    dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
    return dt


def check_and_create_path(path):
    if not os.path.exists(path):
        os.makedirs(path)
        return False
    return True


def check_path(path):
    if not os.path.exists(path):
        return False
    return True


def timestamp_to_time(timestamp):
    time_local = time.localtime(timestamp / 1000)
    dt = time.strftime("%Y年%m月%d日%H点%M分%S秒", time_local)
    return dt


def download_media(path, name, url, type, info=""):
    # 5次错误机会
    for i in range(5):
        try:
            if type == "image":
                print(f"{info}图片开始下载")
                content = requests.get(url).content

                # 임시 파일에 이미지 내용 저장
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    temp_file.write(content)
                    temp_file_path = temp_file.name

                # 이미지 타입 감지
                img_type = imghdr.what(temp_file_path)

                if img_type:
                    ext = "." + img_type
                else:
                    ext = ".jpg"

                with open(path + "/" + name + ext, mode="wb") as f:
                    f.write(content)
                print(f"{info}图片下载完成")
            elif type == "video":
                print(f"{name}开始下载, {url}")
                start_time = time.time()
                res = requests.get(url, stream=True)
                size = 0
                chunk_size = 1024 * 1024
                content_size = int(res.headers["content-length"])
                with open(path + "/" + name + ".mp4", mode="wb") as f:
                    for data in res.iter_content(chunk_size=chunk_size):
                        f.write(data)
                        size += len(data)
                        percentage = size / content_size
                        print(
                            f"\r视频:%.2fMB\t" % (content_size / 1024 / 1024),
                            "下载进度:[%-50s%.2f%%]耗时: %.1fs, "
                            % (
                                ">" * int(50 * percentage),
                                percentage * 100,
                                time.time() - start_time,
                            ),
                            end="",
                        )
                    print(f"{name}下载完成")
            break
        except:
            print(f"第{i+1}次下载失败，重新下载, 剩余{4-i}次机会")
            continue


def handle_profile_info(userId, html_text):
    true, false, null, undefined = True, False, None, None
    info = re.findall(r"<script>window.__INITIAL_STATE__=(.*?)</script>", html_text)[0]
    info = eval(info)
    nickname = info["user"]["userPageData"]["basicInfo"]["nickname"]
    avatar = info["user"]["userPageData"]["basicInfo"]["images"]
    avatar = decodedUniChars(avatar)
    desc = info["user"]["userPageData"]["basicInfo"]["desc"]
    follows = info["user"]["userPageData"]["interactions"][0]["count"]
    fans = info["user"]["userPageData"]["interactions"][1]["count"]
    interaction = info["user"]["userPageData"]["interactions"][2]["count"]
    ipLocation = info["user"]["userPageData"]["basicInfo"]["ipLocation"]
    gender = info["user"]["userPageData"]["basicInfo"]["gender"]
    if gender == 0:
        gender = "男"
    elif gender == 1:
        gender = "女"
    else:
        gender = "未知"
    tags_temp = info["user"]["userPageData"]["tags"]
    tags = []
    for tag in tags_temp:
        try:
            tags.append(tag["name"])
        except:
            pass
    user_detail = User_Detail(
        None,
        userId,
        nickname,
        avatar,
        desc,
        follows,
        fans,
        interaction,
        ipLocation,
        gender,
        tags,
    )
    return user_detail


def save_user_detail(path, user):
    with open(f"{path}/detail.txt", mode="w", encoding="utf-8") as f:
        # 逐行输出到txt里
        f.write(f"主页url: {f'https://www.douyin.com/user/{user.userId}'}\n")
        f.write(f"用户名: {user.nickname}\n")
        f.write(f"介绍: {user.desc}\n")
        f.write(f"关注数量: {user.follows}\n")
        f.write(f"粉丝数量: {user.fans}\n")
        f.write(f"作品被赞和收藏数量: {user.interaction}\n")
        f.write(f"ip地址: {user.ipLocation}\n")
        f.write(f"性别: {user.gender}\n")
        f.write(f"标签: {user.tags}\n")


def save_note_detail(path, note):
    with open(path + "/" + "detail.txt", mode="w", encoding="utf-8") as f:
        # 逐行输出到txt里
        f.write(f"笔记url: {f'https://www.xiaohongshu.com/explore/{note.note_id}'}\n")
        f.write(f"笔记类型: {note.note_type}\n")
        f.write(f"笔记标题: {note.title}\n")
        f.write(f"笔记描述: {note.desc}\n")
        f.write(f"笔记点赞数量: {note.liked_count}\n")
        f.write(f"笔记收藏数量: {note.collected_count}\n")
        f.write(f"笔记评论数量: {note.comment_count}\n")
        f.write(f"笔记分享数量: {note.share_count}\n")
        f.write(f"笔记上传时间: {timestamp_to_str(note.upload_time)}\n")
        f.write(f"笔记标签: {note.tag_list}\n")
        f.write(f"笔记ip归属地: {note.ip_location}\n")


def handle_note_info(data):
    note_id = data["id"]
    note_type = data["note_card"]["type"]
    user_id = data["note_card"]["user"]["user_id"]
    nickname = data["note_card"]["user"]["nickname"]
    avatar = data["note_card"]["user"]["avatar"]
    title = data["note_card"]["title"]
    desc = data["note_card"]["desc"]
    liked_count = data["note_card"]["interact_info"]["liked_count"]
    collected_count = data["note_card"]["interact_info"]["collected_count"]
    comment_count = data["note_card"]["interact_info"]["comment_count"]
    share_count = data["note_card"]["interact_info"]["share_count"]
    if note_type == "video":
        video_addr = (
            "https://sns-video-bd.xhscdn.com/"
            + data["note_card"]["video"]["consumer"]["origin_video_key"]
        )
    else:
        video_addr = ""
    image_list = data["note_card"]["image_list"]
    tags_temp = data["note_card"]["tag_list"]
    tags = []
    for tag in tags_temp:
        try:
            tags.append(tag["name"])
        except:
            pass
    upload_time = data["note_card"]["time"]
    if "ip_location" in data["note_card"]:
        ip_location = data["note_card"]["ip_location"]
    else:
        ip_location = "未知"
    note_detail = Note_Detail(
        None,
        note_id,
        note_type,
        user_id,
        nickname,
        avatar,
        title,
        desc,
        liked_count,
        collected_count,
        comment_count,
        share_count,
        video_addr,
        image_list,
        tags,
        upload_time,
        ip_location,
    )
    return note_detail


def get_cookies():
    return {
        "xsecappid": "",
        "a1": "",
        "webId": "",
        "gid": "",
        "webBuild": "3.3.4",
        "web_session": "",
        "websectiga": "",
        "sec_poison_id": "",
    }


def get_home_headers():
    return {
        "authority": "www.xiaohongshu.com",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "sec-ch-ua": '"Microsoft Edge";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.47",
    }


def get_headers():
    return {
        "authority": "edith.xiaohongshu.com",
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "content-type": "application/json;charset=UTF-8",
        "origin": "https://www.xiaohongshu.com",
        "referer": "https://www.xiaohongshu.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.188",
        "x-s": "",
        "x-t": "",
    }


def get_note_data(note_id):
    return {"source_note_id": note_id, "image_scenes": ["CRD_PRV_WEBP", "CRD_WM_WEBP"]}


def get_search_data():
    return {
        "image_scenes": "FD_PRV_WEBP,FD_WM_WEBP",
        "keyword": "",
        "note_type": "0",
        "page": "",
        "page_size": "20",
        "search_id": "2c7hu5b3kzoivkh848hp0",
        "sort": "general",
    }


def get_params():
    return {"num": "30", "cursor": "", "user_id": "", "image_scenes": ""}


def check_cookies():
    more_url = "https://edith.xiaohongshu.com/api/sns/web/v1/user_posted"
    params = get_params()
    headers = get_headers()
    try:
        if not os.path.exists("./static/cookies.txt"):
            raise Exception("获取cookie")
        test_user_id = "5ad2ede14eacab146f865fe9"
        with open("./static/cookies.txt", "r", encoding="utf-8") as f:
            cookies_obj = f.read()
        cookies_local = eval(cookies_obj)
        params["user_id"] = test_user_id
        params["cursor"] = ""
        api = f"/api/sns/web/v1/user_posted?num=30&cursor=&user_id={test_user_id}&image_scenes="
        a1 = cookies_local["a1"]
        try:
            ret = js.call("get_xs", api, "", a1)
        except:
            print("缺少nodejs环境")
            return
        headers["x-s"], headers["x-t"] = ret["X-s"], str(ret["X-t"])
        response = requests.get(
            more_url, headers=headers, cookies=cookies_local, params=params
        )
        res = response.json()
        if not res["success"]:
            raise Exception("cookie失效")
        else:
            print("cookie有效")
            return cookies_local
    except:
        print("cookie失效，请手动更改cookies.txt文件")
        sys.exit(1)

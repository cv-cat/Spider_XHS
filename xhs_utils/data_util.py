import csv
import json
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path

import openpyxl
import requests
from loguru import logger
from retry import retry

from xhs_utils.http_util import REQUEST_TIMEOUT

_AGE_TAG_PATTERNS = ["60后", "65后", "70后", "75后", "80后", "85后", "90后", "95后", "00后", "05后", "10后"]
_AGE_DESC_RE = re.compile(r'(\d{1,2})\s*岁')

# 年代标签 → 出生年份区间（左闭右闭）
_GENERATION_BIRTH_YEAR: dict[str, tuple[int, int]] = {
    "60后": (1960, 1969), "65后": (1965, 1974),
    "70后": (1970, 1979), "75后": (1975, 1984),
    "80后": (1980, 1989), "85后": (1985, 1994),
    "90后": (1990, 1999), "95后": (1995, 2004),
    "00后": (2000, 2009), "05后": (2005, 2014),
    "10后": (2010, 2019),
}


def norm_str(value):
    new_str = re.sub(r"[\\/:*?\"<>| ]+", "", value).replace('\n', '').replace('\r', '')
    return new_str

def norm_text(text):
    ILLEGAL_CHARACTERS_RE = re.compile(r'[\000-\010]|[\013-\014]|[\016-\037]')
    text = ILLEGAL_CHARACTERS_RE.sub(r'', text)
    return text


def timestamp_to_str(timestamp):
    time_local = time.localtime(timestamp / 1000)
    dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
    return dt

def handle_user_info(data, user_id):
    home_url = f'https://www.xiaohongshu.com/user/profile/{user_id}'
    nickname = data['basic_info']['nickname']
    avatar = data['basic_info']['imageb']
    red_id = data['basic_info']['red_id']
    gender = data['basic_info']['gender']
    if gender == 0:
        gender = '男'
    elif gender == 1:
        gender = '女'
    else:
        gender = '未知'
    ip_location = data['basic_info']['ip_location']
    desc = data['basic_info']['desc']
    follows = data['interactions'][0]['count']
    fans = data['interactions'][1]['count']
    interaction = data['interactions'][2]['count']
    tags_temp = data['tags']
    tags = []
    for tag in tags_temp:
        try:
            tags.append(tag['name'])
        except (KeyError, TypeError):
            pass
    user = {
        'user_id': user_id,
        'home_url': home_url,
        'nickname': nickname,
        'avatar': avatar,
        'red_id': red_id,
        'gender': gender,
        'ip_location': ip_location,
        'desc': desc,
        'follows': follows,
        'fans': fans,
        'interaction': interaction,
        'tags': tags,
    }
    user['age_info'] = extract_age_info(user)
    return user

def handle_note_info(data):
    note_id = data['id']
    note_url = data['url']
    note_type = data['note_card']['type']
    if note_type == 'normal':
        note_type = '图集'
    else:
        note_type = '视频'
    user_id = data['note_card']['user']['user_id']
    home_url = f'https://www.xiaohongshu.com/user/profile/{user_id}'
    nickname = data['note_card']['user']['nickname']
    avatar = data['note_card']['user']['avatar']
    title = data['note_card']['title']
    if title.strip() == '':
        title = f'无标题'
    desc = data['note_card']['desc']
    liked_count = data['note_card']['interact_info']['liked_count']
    collected_count = data['note_card']['interact_info']['collected_count']
    comment_count = data['note_card']['interact_info']['comment_count']
    share_count = data['note_card']['interact_info']['share_count']
    image_list_temp = data['note_card']['image_list']
    image_list = []
    for image in image_list_temp:
        try:
            image_list.append(image['info_list'][1]['url'])
            # success, msg, img_url = XHS_Apis.get_note_no_water_img(image['info_list'][1]['url'])
            # image_list.append(img_url)
        except (KeyError, IndexError, TypeError):
            pass
    if note_type == '视频':
        video_cover = image_list[0] if image_list else None
        video_addr = None
        video_info = data.get('note_card', {}).get('video', {})
        streams = video_info.get('media', {}).get('stream', {}).get('h264', [])
        if streams:
            video_addr = streams[0].get('master_url') or streams[0].get('url')
        if not video_addr and 'consumer' in video_info:
            origin_key = video_info['consumer'].get('origin_video_key')
            if origin_key:
                video_addr = f"https://sns-video-bd.xhscdn.com/{origin_key}"
    else:
        video_cover = None
        video_addr = None
    tags_temp = data['note_card']['tag_list']
    tags = []
    for tag in tags_temp:
        try:
            tags.append(tag['name'])
        except (KeyError, TypeError):
            pass
    upload_time = timestamp_to_str(data['note_card']['time'])
    if 'ip_location' in data['note_card']:
        ip_location = data['note_card']['ip_location']
    else:
        ip_location = '未知'
    return {
        'note_id': note_id,
        'note_url': note_url,
        'note_type': note_type,
        'user_id': user_id,
        'home_url': home_url,
        'nickname': nickname,
        'avatar': avatar,
        'title': title,
        'desc': desc,
        'liked_count': liked_count,
        'collected_count': collected_count,
        'comment_count': comment_count,
        'share_count': share_count,
        'video_cover': video_cover,
        'video_addr': video_addr,
        'image_list': image_list,
        'tags': tags,
        'upload_time': upload_time,
        'ip_location': ip_location,
    }

def handle_comment_info(data):
    note_id = data['note_id']
    note_url = data['note_url']
    comment_id = data['id']
    user_id = data['user_info']['user_id']
    home_url = f'https://www.xiaohongshu.com/user/profile/{user_id}'
    nickname = data['user_info']['nickname']
    avatar = data['user_info']['image']
    content = data['content']
    show_tags = data['show_tags']
    like_count = data['like_count']
    upload_time = timestamp_to_str(data['create_time'])
    try:
        ip_location = data['ip_location']
    except KeyError:
        ip_location = '未知'
    pictures = []
    try:
        pictures_temp = data['pictures']
        for picture in pictures_temp:
            try:
                pictures.append(picture['info_list'][1]['url'])
                # success, msg, img_url = XHS_Apis.get_note_no_water_img(picture['info_list'][1]['url'])
                # pictures.append(img_url)
            except (KeyError, IndexError, TypeError):
                pass
    except (KeyError, TypeError):
        pass
    return {
        'note_id': note_id,
        'note_url': note_url,
        'comment_id': comment_id,
        'user_id': user_id,
        'home_url': home_url,
        'nickname': nickname,
        'avatar': avatar,
        'content': content,
        'show_tags': show_tags,
        'like_count': like_count,
        'upload_time': upload_time,
        'ip_location': ip_location,
        'pictures': pictures,
    }
def save_to_xlsx(datas, file_path, type='note'):
    wb = openpyxl.Workbook()
    ws = wb.active
    if type == 'note':
        headers = ['笔记id', '笔记url', '笔记类型', '用户id', '用户主页url', '昵称', '头像url', '标题', '描述', '点赞数量', '收藏数量', '评论数量', '分享数量', '视频封面url', '视频地址url', '图片地址url列表', '标签', '上传时间', 'ip归属地']
    elif type == 'user':
        headers = ['用户id', '用户主页url', '用户名', '头像url', '小红书号', '性别', 'ip地址', '介绍', '关注数量', '粉丝数量', '作品被赞和收藏数量', '标签']
    else:
        headers = ['笔记id', '笔记url', '评论id', '用户id', '用户主页url', '昵称', '头像url', '评论内容', '评论标签', '点赞数量', '上传时间', 'ip归属地', '图片地址url列表']
    field_keys = {
        'note': ['note_id', 'note_url', 'note_type', 'user_id', 'home_url', 'nickname', 'avatar', 'title', 'desc', 'liked_count', 'collected_count', 'comment_count', 'share_count', 'video_cover', 'video_addr', 'image_list', 'tags', 'upload_time', 'ip_location'],
        'user': ['user_id', 'home_url', 'nickname', 'avatar', 'red_id', 'gender', 'ip_location', 'desc', 'follows', 'fans', 'interaction', 'tags'],
        'comment': ['note_id', 'note_url', 'comment_id', 'user_id', 'home_url', 'nickname', 'avatar', 'content', 'show_tags', 'like_count', 'upload_time', 'ip_location', 'pictures'],
    }
    keys = field_keys.get(type, field_keys['comment'])
    ws.append(headers)
    for data in datas:
        ws.append([norm_text(str(data.get(key, ''))) for key in keys])
    wb.save(file_path)
    logger.info(f'数据保存至 {file_path}')

_CSV_FIELDS = {
    'comment': {
        'headers': ['发布时间', '用户主页url', 'ip归属地'],
        'keys': ['upload_time', 'home_url', 'ip_location'],
    },
    'user': {
        'headers': ['用户id', '用户主页url', '昵称', '小红书号', '性别', '年龄信息', 'ip归属地', '介绍', '关注数量', '粉丝数量', '获赞收藏数', '标签', '交友倾向', '判断理由'],
        'keys': ['user_id', 'home_url', 'nickname', 'red_id', 'gender', 'age_info', 'ip_location', 'desc', 'follows', 'fans', 'interaction', 'tags', 'dating_tendency', 'dating_reason'],
    },
}


def save_to_csv(datas: list, file_path: str, type: str = 'user') -> None:
    fields = _CSV_FIELDS.get(type, _CSV_FIELDS['user'])
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fields['headers'])
        writer.writeheader()
        for data in datas:
            row = {
                header: norm_text(str(data.get(key, '')))
                for header, key in zip(fields['headers'], fields['keys'])
            }
            writer.writerow(row)
    logger.info(f'数据保存至 {file_path}')


def extract_age_info(user: dict) -> str:
    for tag in (user.get('tags') or []):
        tag_str = str(tag)
        for pattern in _AGE_TAG_PATTERNS:
            if pattern in tag_str:
                return pattern
    desc = user.get('desc') or ''
    match = _AGE_DESC_RE.search(desc)
    if match:
        return f"{match.group(1)}岁"
    return '未知'


def filter_comments(
    comments: list,
    regions: list[str] | None = None,
    days: int | None = None,
) -> list:
    now = datetime.now()
    result = []
    for c in comments:
        if regions:
            ip_loc = c.get('ip_location') or ''
            if not any(ip_loc.startswith(r) or r in ip_loc for r in regions):
                continue
        if days is not None:
            try:
                comment_time = datetime.strptime(c['upload_time'], '%Y-%m-%d %H:%M:%S')
                if now - comment_time > timedelta(days=days):
                    continue
            except (KeyError, ValueError):
                pass
        result.append(c)
    return result


def _age_in_range(age_info: str, min_age: int, max_age: int) -> bool:
    """判断 age_info（'X岁' 或 '90后' 等）是否落在 [min_age, max_age] 内。"""
    m = _AGE_DESC_RE.match(age_info)
    if m:
        return min_age <= int(m.group(1)) <= max_age
    current_year = datetime.now().year
    for tag, (birth_start, birth_end) in _GENERATION_BIRTH_YEAR.items():
        if tag in age_info:
            # 年代标签对应的年龄区间（当前年份估算）
            age_min = current_year - birth_end
            age_max = current_year - birth_start
            return age_min <= max_age and age_max >= min_age
    return False


def filter_users(
    users: list,
    genders: list[str] | None = None,
    age_range: tuple[int, int] | None = None,
    fans_max: int | None = None,
) -> list:
    result = []
    for u in users:
        if genders and u.get('gender') not in genders:
            continue
        if age_range is not None:
            age_info = u.get('age_info', '未知')
            if age_info == '未知' or not _age_in_range(age_info, *age_range):
                continue
        if fans_max is not None:
            try:
                if int(u.get('fans', 0)) >= fans_max:
                    continue
            except (ValueError, TypeError):
                pass
        result.append(u)
    return result


def download_media(path, name, url, type):
    if not url:
        raise ValueError(f'{type} url is empty: {name}')
    file_path = Path(path) / f'{name}.{"jpg" if type == "image" else "mp4"}'
    if type == 'image':
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        content = response.content
        with open(file_path, mode="wb") as f:
            f.write(content)
    elif type == 'video':
        res = requests.get(url, stream=True, timeout=REQUEST_TIMEOUT)
        res.raise_for_status()
        size = 0
        chunk_size = 1024 * 1024
        with open(file_path, mode="wb") as f:
            for data in res.iter_content(chunk_size=chunk_size):
                f.write(data)
                size += len(data)

def save_user_detail(user, path):
    with open(Path(path) / 'detail.txt', mode="w", encoding="utf-8") as f:
        # 逐行输出到txt里
        f.write(f"用户id: {user['user_id']}\n")
        f.write(f"用户主页url: {user['home_url']}\n")
        f.write(f"用户名: {user['nickname']}\n")
        f.write(f"头像url: {user['avatar']}\n")
        f.write(f"小红书号: {user['red_id']}\n")
        f.write(f"性别: {user['gender']}\n")
        f.write(f"ip地址: {user['ip_location']}\n")
        f.write(f"介绍: {user['desc']}\n")
        f.write(f"关注数量: {user['follows']}\n")
        f.write(f"粉丝数量: {user['fans']}\n")
        f.write(f"作品被赞和收藏数量: {user['interaction']}\n")
        f.write(f"标签: {user['tags']}\n")

def save_note_detail(note, path):
    with open(Path(path) / 'detail.txt', mode="w", encoding="utf-8") as f:
        # 逐行输出到txt里
        f.write(f"笔记id: {note['note_id']}\n")
        f.write(f"笔记url: {note['note_url']}\n")
        f.write(f"笔记类型: {note['note_type']}\n")
        f.write(f"用户id: {note['user_id']}\n")
        f.write(f"用户主页url: {note['home_url']}\n")
        f.write(f"昵称: {note['nickname']}\n")
        f.write(f"头像url: {note['avatar']}\n")
        f.write(f"标题: {note['title']}\n")
        f.write(f"描述: {note['desc']}\n")
        f.write(f"点赞数量: {note['liked_count']}\n")
        f.write(f"收藏数量: {note['collected_count']}\n")
        f.write(f"评论数量: {note['comment_count']}\n")
        f.write(f"分享数量: {note['share_count']}\n")
        f.write(f"视频封面url: {note['video_cover']}\n")
        f.write(f"视频地址url: {note['video_addr']}\n")
        f.write(f"图片地址url列表: {note['image_list']}\n")
        f.write(f"标签: {note['tags']}\n")
        f.write(f"上传时间: {note['upload_time']}\n")
        f.write(f"ip归属地: {note['ip_location']}\n")



@retry(tries=3, delay=1)
def download_note(note_info, path, save_choice):
    note_id = note_info['note_id']
    user_id = note_info['user_id']
    title = note_info['title']
    title = norm_str(title)[:40]
    nickname = note_info['nickname']
    nickname = norm_str(nickname)[:20]
    if title.strip() == '':
        title = f'无标题'
    save_path = str(Path(path) / f'{nickname}_{user_id}' / f'{title}_{note_id}')
    check_and_create_path(save_path)
    with open(Path(save_path) / 'info.json', mode='w', encoding='utf-8') as f:
        f.write(json.dumps(note_info) + '\n')
    note_type = note_info['note_type']
    save_note_detail(note_info, save_path)
    if note_type == '图集' and save_choice in ['media', 'media-image', 'all']:
        for img_index, img_url in enumerate(note_info['image_list']):
            download_media(save_path, f'image_{img_index}', img_url, 'image')
    elif note_type == '视频' and save_choice in ['media', 'media-video', 'all']:
        if note_info.get('video_cover'):
            download_media(save_path, 'cover', note_info['video_cover'], 'image')
        else:
            logger.warning(f"video cover url is empty: {note_id}")
        if note_info.get('video_addr'):
            download_media(save_path, 'video', note_info['video_addr'], 'video')
        else:
            logger.warning(f"video url is empty: {note_id}")
    return save_path


def check_and_create_path(path):
    Path(path).mkdir(parents=True, exist_ok=True)

import json
import os
import random
import time
from datetime import datetime
from loguru import logger
from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.common_util import init
from xhs_utils.data_util import (
    handle_note_info, handle_user_info, handle_comment_info,
    download_note, save_to_xlsx,
    filter_comments, filter_users, save_to_csv,
)
from xhs_utils.http_util import random_delay, rate_limited_delay, reset_request_counter
from xhs_utils.llm_util import analyze_dating_tendency, is_marketing_account


class SessionExpiredError(Exception):
    pass


_SESSION_EXPIRED_KEYWORDS = ('登录已过期', '登录失效', '未登录', 'login_required', 'auth_required')


def _is_session_expired(msg: str) -> bool:
    s = str(msg).lower()
    return any(kw in s for kw in _SESSION_EXPIRED_KEYWORDS) or ('登录' in s and ('过期' in s or '失效' in s))


class Data_Spider():
    def __init__(self):
        self.xhs_apis = XHS_Apis()
        self._last_keepalive: float = time.time()

    def check_session(self, cookies_str: str, proxies=None) -> None:
        """快速探测 cookie 是否有效，无效则抛出 SessionExpiredError。"""
        success, msg, _ = self.xhs_apis.get_homefeed_all_channel(cookies_str, proxies)
        if not success:
            if _is_session_expired(msg):
                raise SessionExpiredError(f'Cookie 已失效: {msg}')
            logger.warning(f'[Session] 探测失败（非登录问题）: {msg}')

    def _maybe_keepalive(self, cookies_str: str, proxies=None, interval: float = 600.0) -> None:
        """距上次心跳超过 interval 秒时，发一次轻量请求保持 session 活跃。"""
        if time.time() - self._last_keepalive >= interval:
            logger.debug('[Keepalive] 发送心跳请求')
            try:
                self.xhs_apis.get_homefeed_all_channel(cookies_str, proxies)
            except Exception as e:
                logger.warning(f'[Keepalive] 心跳请求异常: {e}')
            self._last_keepalive = time.time()

    def spider_note(self, note_url: str, cookies_str: str, proxies=None):
        """
        爬取一个笔记的信息
        :param note_url:
        :param cookies_str:
        :return:
        """
        note_info = None
        try:
            success, msg, note_info = self.xhs_apis.get_note_info(note_url, cookies_str, proxies)
            if success:
                note_info = note_info['data']['items'][0]
                note_info['url'] = note_url
                note_info = handle_note_info(note_info)
        except Exception as e:
            success = False
            msg = e
        logger.info(f'爬取笔记信息 {note_url}: {success}, msg: {msg}')
        return success, msg, note_info

    def spider_some_note(self, notes: list, cookies_str: str, base_path: dict, save_choice: str, excel_name: str = '', proxies=None):
        """
        爬取一些笔记的信息
        :param notes:
        :param cookies_str:
        :param base_path:
        :return:
        """
        if (save_choice == 'all' or save_choice == 'excel') and excel_name == '':
            raise ValueError('excel_name 不能为空')
        note_list = []
        for note_url in notes:
            success, msg, note_info = self.spider_note(note_url, cookies_str, proxies)
            if note_info is not None and success:
                note_list.append(note_info)
        for note_info in note_list:
            if save_choice == 'all' or 'media' in save_choice:
                download_note(note_info, base_path['media'], save_choice)
        if save_choice == 'all' or save_choice == 'excel':
            file_path = os.path.abspath(os.path.join(base_path['excel'], f'{excel_name}.xlsx'))
            save_to_xlsx(note_list, file_path)


    def spider_user_all_note(self, user_url: str, cookies_str: str, base_path: dict, save_choice: str, excel_name: str = '', proxies=None):
        """
        爬取一个用户的所有笔记
        :param user_url:
        :param cookies_str:
        :param base_path:
        :return:
        """
        note_list = []
        try:
            success, msg, all_note_info = self.xhs_apis.get_user_all_notes(user_url, cookies_str, proxies)
            if success:
                logger.info(f'用户 {user_url} 作品数量: {len(all_note_info)}')
                for simple_note_info in all_note_info:
                    note_url = f"https://www.xiaohongshu.com/explore/{simple_note_info['note_id']}?xsec_token={simple_note_info['xsec_token']}"
                    note_list.append(note_url)
            if save_choice == 'all' or save_choice == 'excel':
                excel_name = user_url.split('/')[-1].split('?')[0]
            self.spider_some_note(note_list, cookies_str, base_path, save_choice, excel_name, proxies)
        except Exception as e:
            success = False
            msg = e
        logger.info(f'爬取用户所有视频 {user_url}: {success}, msg: {msg}')
        return note_list, success, msg

    def spider_some_search_note(self, query: str, require_num: int, cookies_str: str, base_path: dict, save_choice: str, sort_type_choice=0, note_type=0, note_time=0, note_range=0, pos_distance=0, geo: dict = None,  excel_name: str = '', proxies=None):
        """
            指定数量搜索笔记，设置排序方式和笔记类型和笔记数量
            :param query 搜索的关键词
            :param require_num 搜索的数量
            :param cookies_str 你的cookies
            :param base_path 保存路径
            :param sort_type_choice 排序方式 0 综合排序, 1 最新, 2 最多点赞, 3 最多评论, 4 最多收藏
            :param note_type 笔记类型 0 不限, 1 视频笔记, 2 普通笔记
            :param note_time 笔记时间 0 不限, 1 一天内, 2 一周内天, 3 半年内
            :param note_range 笔记范围 0 不限, 1 已看过, 2 未看过, 3 已关注
            :param pos_distance 位置距离 0 不限, 1 同城, 2 附近 指定这个必须要指定 geo
            返回搜索的结果
        """
        note_list = []
        try:
            success, msg, notes = self.xhs_apis.search_some_note(query, require_num, cookies_str, sort_type_choice, note_type, note_time, note_range, pos_distance, geo, proxies)
            if success:
                notes = list(filter(lambda x: x['model_type'] == "note", notes))
                logger.info(f'搜索关键词 {query} 笔记数量: {len(notes)}')
                for note in notes:
                    note_url = f"https://www.xiaohongshu.com/explore/{note['id']}?xsec_token={note['xsec_token']}"
                    note_list.append(note_url)
            if save_choice == 'all' or save_choice == 'excel':
                excel_name = query
            self.spider_some_note(note_list, cookies_str, base_path, save_choice, excel_name, proxies)
        except Exception as e:
            success = False
            msg = e
        logger.info(f'搜索关键词 {query} 笔记: {success}, msg: {msg}')
        return note_list, success, msg

    def spider_keyword_to_users(
        self,
        query: str,
        cookies_str: str,
        base_path: dict,
        note_num: int = 100,
        comment_filter_regions: list = None,
        comment_filter_days: int = 7,
        user_filter_genders: list = None,
        user_filter_age_range: tuple = None,
        user_filter_fans_max: int = None,
        delay_range: tuple = (5.0, 15.0),
        cooldown_every: int = 10,
        cooldown_range: tuple = (60.0, 120.0),
        proxies: dict = None,
    ):
        """
        关键词搜索 → 爬评论 → 过滤用户 → 拉用户信息 → 过滤 → 保存 CSV

        :param query                   搜索关键词
        :param cookies_str             Cookie 字符串
        :param base_path               保存路径 dict，含 excel key
        :param note_num                爬取笔记数量，默认 100
        :param comment_filter_regions  省份列表，如 ["北京"]，None 表示不过滤
        :param comment_filter_days     最近 N 天，默认 7 天，None 表示不过滤
        :param user_filter_genders     性别列表，如 ["女"]，None 表示不过滤
        :param user_filter_age_range   年龄区间 (min, max)，如 (35, 45)，None 表示不过滤
        :param user_filter_fans_max    粉丝数上限（不含），如 1000，None 表示不过滤
        :param delay_range             每次请求间随机延迟范围 (min_s, max_s)，默认 5~15s
        :param cooldown_every          每隔 N 次请求触发一次长冷却，默认 10
        :param cooldown_range          长冷却时长范围 (min_s, max_s)，默认 60~120s
        :param proxies                 代理配置
        """
        reset_request_counter()
        all_filtered_comments = []
        all_final_users = []
        seen_user_ids: set = set()

        # 健康检查：pipeline 启动前确认 cookie 有效
        logger.info('[Pipeline] 校验 Cookie 有效性...')
        self.check_session(cookies_str, proxies)
        self._last_keepalive = time.time()
        logger.info('[Pipeline] Cookie 有效')

        # Step 1: 按时间排序搜索笔记
        logger.info(f'[Pipeline] 搜索关键词: {query}，数量: {note_num}')
        success, msg, notes = self.xhs_apis.search_some_note(
            query, note_num, cookies_str,
            sort_type_choice=1,  # 最新
            note_type=2,         # 只要图文，过滤视频
            proxies=proxies,
        )
        if not success:
            if _is_session_expired(msg):
                raise SessionExpiredError(f'搜索时 Cookie 失效: {msg}')
            logger.error(f'[Pipeline] 搜索失败: {msg}')
            return [], [], False, msg

        def _note_comment_count(n: dict) -> int:
            try:
                return int(n.get('note_card', {}).get('interact_info', {}).get('comment_count', 0) or 0)
            except (ValueError, TypeError):
                return 0

        valid_notes = [n for n in notes if n.get('model_type') == 'note' and _note_comment_count(n) > 0]
        skipped = len([n for n in notes if n.get('model_type') == 'note']) - len(valid_notes)
        if skipped:
            logger.info(f'[Pipeline] 跳过零评论笔记 {skipped} 篇')
        random.shuffle(valid_notes)
        logger.info(f'[Pipeline] 有效笔记 {len(valid_notes)} 篇（已打乱顺序），开始深度优先处理')

        # 深度优先：每篇笔记独立走完 评论→过滤→用户→LLM 全流程
        for note in valid_notes:
            note_url = f"https://www.xiaohongshu.com/explore/{note['id']}?xsec_token={note['xsec_token']}"

            # Step 2: 拉取本篇笔记评论
            self._maybe_keepalive(cookies_str, proxies)
            rate_limited_delay(*delay_range, cooldown_every=cooldown_every,
                               cooldown_min=cooldown_range[0], cooldown_max=cooldown_range[1])
            success, msg, out_comments = self.xhs_apis.get_note_all_comment(note_url, cookies_str, proxies)
            if not success:
                if _is_session_expired(msg):
                    raise SessionExpiredError(f'爬评论时 Cookie 失效: {msg}')
                logger.warning(f'[Pipeline] 评论获取失败 {note_url}: {msg}')
                continue

            note_comments = []
            for comment in out_comments:
                note_comments.append(handle_comment_info({**comment, 'note_url': note_url}))
                for sub in comment.get('sub_comments', []):
                    note_comments.append(handle_comment_info({**sub, 'note_url': note_url}))

            # Step 3: 按省份 + 时间过滤本篇评论
            filtered = filter_comments(note_comments, comment_filter_regions, comment_filter_days)
            all_filtered_comments.extend(filtered)

            # Steps 4-6: 对本篇新出现的候选用户逐一完成全流程
            for c in filtered:
                uid = c.get('user_id')
                if not uid or uid in seen_user_ids:
                    continue
                seen_user_ids.add(uid)

                # Step 4: 拉取用户信息
                self._maybe_keepalive(cookies_str, proxies)
                rate_limited_delay(*delay_range, cooldown_every=cooldown_every,
                                   cooldown_min=cooldown_range[0], cooldown_max=cooldown_range[1])
                success, msg, res_json = self.xhs_apis.get_user_info(uid, cookies_str, proxies)
                if not success or not res_json:
                    if _is_session_expired(msg):
                        raise SessionExpiredError(f'拉用户信息时 Cookie 失效: {msg}')
                    logger.warning(f'[Pipeline] 用户信息获取失败 {uid}: {msg}')
                    continue
                try:
                    user_info = handle_user_info(res_json['data'], uid)
                except Exception as e:
                    logger.warning(f'[Pipeline] 用户信息解析失败 {uid}: {e}')
                    continue

                # Step 5: 人口属性过滤（性别 / 年龄 / 粉丝数）
                if not filter_users([user_info], user_filter_genders, user_filter_age_range, user_filter_fans_max):
                    continue

                # Step 5b: LLM 过滤营销号
                mkt = is_marketing_account(user_info.get('nickname', ''), user_info.get('desc', ''), user_info.get('tags', []))
                if mkt.get('is_marketing'):
                    logger.info(f'[Pipeline] 过滤营销号 {user_info["nickname"]}: {mkt.get("reason", "")}')
                    continue

                # Step 6: 拉取用户笔记标题 → LLM 分析交友倾向
                note_titles = []
                try:
                    self._maybe_keepalive(cookies_str, proxies)
                    rate_limited_delay(*delay_range, cooldown_every=cooldown_every,
                                       cooldown_min=cooldown_range[0], cooldown_max=cooldown_range[1])
                    success, msg, nres = self.xhs_apis.get_user_note_info(uid, '', cookies_str, proxies=proxies)
                    if success and nres:
                        for n in nres.get('data', {}).get('notes', [])[:10]:
                            title = (
                                n.get('display_title') or n.get('title')
                                or n.get('note_card', {}).get('display_title', '')
                                or n.get('note_card', {}).get('title', '')
                            )
                            if title:
                                note_titles.append(title)
                except Exception as e:
                    logger.warning(f'[Pipeline] 获取笔记标题失败 {uid}: {e}')

                tendency = analyze_dating_tendency(user_info.get('desc', ''), note_titles)
                user_info['dating_tendency'] = tendency.get('tendency', '未分析')
                user_info['dating_reason'] = tendency.get('reason', '')
                all_final_users.append(user_info)
                logger.info(f'[Pipeline] 新增用户 {user_info["nickname"]} → {user_info["dating_tendency"]}')

        logger.info(f'[Pipeline] 完成。过滤评论 {len(all_filtered_comments)} 条，最终用户 {len(all_final_users)} 人')

        # Step 7: 保存 CSV
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_query = query.replace('/', '_').replace('\\', '_')[:20]
        comment_csv = os.path.join(base_path['excel'], f'{safe_query}_评论_{ts}.csv')
        user_csv = os.path.join(base_path['excel'], f'{safe_query}_用户_{ts}.csv')
        save_to_csv(all_filtered_comments, comment_csv, type='comment')
        save_to_csv(all_final_users, user_csv, type='user')

        return all_filtered_comments, all_final_users, True, 'ok'


if __name__ == '__main__':
    """
        此文件为爬虫的入口文件，可以直接运行
        apis/xhs_pc_apis.py 为爬虫的api文件，包含小红书的全部数据接口，可以继续封装
        apis/xhs_creator_apis.py 为小红书创作者中心的api文件
        感谢star和follow
    """

    cookies_str, base_path = init()
    data_spider = Data_Spider()
    """
        save_choice: all: 保存所有的信息, media: 保存视频和图片（media-video只下载视频, media-image只下载图片，media都下载）, excel: 保存到excel
        save_choice 为 excel 或者 all 时，excel_name 不能为空
    """


    # 4 关键词搜索 → 评论 → 过滤用户 → 保存 CSV
    try:
        data_spider.spider_keyword_to_users(
            query="读书搭子",
            cookies_str=cookies_str,
            base_path=base_path,
            note_num=100,                    # 拉最新 100 篇笔记
            comment_filter_regions=["北京"], # 只保留北京 IP 的评论
            comment_filter_days=7,           # 最近一周
            user_filter_genders=["女"],      # 只保留女性
            user_filter_age_range=(35, 45),  # 年龄 35-45 岁
            user_filter_fans_max=1000,       # 粉丝数 < 1000
            delay_range=(5.0, 15.0),      # 每次请求随机等待 5~15s
            cooldown_every=10,            # 每 10 次触发冷却
            cooldown_range=(60.0, 120.0), # 冷却 60~120s
        )
    except SessionExpiredError as e:
        logger.error(f'[Pipeline] Cookie 已失效，请重新获取 Cookie 后重试。详情: {e}')

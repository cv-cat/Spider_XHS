import json
import re

from loguru import logger

_MODEL = 'qwen2.5:7b'

_SYSTEM_PROMPT = """你是一个分析小红书用户内容的助手。
根据用户的个人简介和笔记标题列表，判断该用户是否有交友/约会意愿。

请只输出以下 JSON 格式，不要输出其他任何内容：
{"tendency": "有", "reason": "一句话说明"}

tendency 只能取以下三个值之一：
- 有：简介或笔记中出现找朋友、交友、脱单、相亲、单身想认识人、寻缘、约见等明确社交/情感信号
- 无：内容以分享生活/知识/好物为主，无情感社交信号
- 不确定：信号模糊、内容太少或无法判断"""


def _extract_json(text: str) -> dict:
    match = re.search(r'\{[^{}]+\}', text, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise ValueError(f'响应中未找到 JSON: {text[:200]}')


_MARKETING_PROMPT = """你是一个小红书账号真实性分析助手。
根据用户昵称、简介和标签，判断该账号是否为营销号、广告号或商业推广账号。

营销号的典型特征（满足其一即可）：
- 昵称或简介含有：微信/vx/wx/威/薇、代购、招募、商务合作、推广、接单、店铺、官方、加我、引流
- 简介像广告文案，大量使用感叹号或促销话术
- 整体内容以产品销售、引流变现为核心目的

请只输出以下 JSON 格式，不要输出任何其他内容：
{"is_marketing": true或false, "reason": "一句话理由"}"""


def is_marketing_account(nickname: str, desc: str, tags: list[str]) -> dict:
    """
    判断用户是否为营销号。

    :param nickname  用户昵称
    :param desc      个人简介
    :param tags      标签列表
    :return {"is_marketing": bool, "reason": str}
    """
    try:
        import ollama
    except ImportError:
        logger.error('ollama 包未安装，请执行: pip install ollama')
        return {'is_marketing': False, 'reason': 'ollama 包未安装'}

    tags_str = '、'.join(str(t) for t in (tags or [])[:10]) or '无'
    user_message = (
        f"昵称：{nickname.strip() or '（无）'}\n"
        f"简介：{(desc or '').strip() or '（未填写）'}\n"
        f"标签：{tags_str}"
    )

    try:
        resp = ollama.chat(
            model=_MODEL,
            messages=[
                {'role': 'system', 'content': _MARKETING_PROMPT},
                {'role': 'user', 'content': user_message},
            ],
            options={'temperature': 0.0},
        )
        content = resp['message']['content'].strip()
        return _extract_json(content)
    except json.JSONDecodeError as e:
        logger.warning(f'营销号判断 JSON 解析失败: {e}')
        return {'is_marketing': False, 'reason': '响应格式异常'}
    except Exception as e:
        logger.warning(f'营销号判断失败: {e}')
        return {'is_marketing': False, 'reason': str(e)[:120]}


def analyze_dating_tendency(user_desc: str, note_titles: list[str]) -> dict:
    """
    分析用户交友倾向。

    :param user_desc    用户个人简介
    :param note_titles  用户笔记标题列表（最多取前 10 条）
    :return {"tendency": "有/无/不确定", "reason": "..."}
    """
    try:
        import ollama
    except ImportError:
        logger.error('ollama 包未安装，请执行: pip install ollama')
        return {'tendency': '未分析', 'reason': 'ollama 包未安装'}

    titles_text = '\n'.join(f'- {t}' for t in note_titles[:10] if str(t).strip())
    if not titles_text:
        titles_text = '（无笔记内容）'

    user_message = (
        f"个人简介：{user_desc.strip() or '（未填写）'}\n\n"
        f"笔记标题：\n{titles_text}"
    )

    try:
        resp = ollama.chat(
            model=_MODEL,
            messages=[
                {'role': 'system', 'content': _SYSTEM_PROMPT},
                {'role': 'user', 'content': user_message},
            ],
            options={'temperature': 0.1},
        )
        content = resp['message']['content'].strip()
        return _extract_json(content)
    except json.JSONDecodeError as e:
        logger.warning(f'LLM 响应 JSON 解析失败: {e}')
        return {'tendency': '不确定', 'reason': '响应格式异常'}
    except Exception as e:
        logger.warning(f'LLM 分析失败: {e}')
        return {'tendency': '未分析', 'reason': str(e)[:120]}

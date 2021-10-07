import os
import time

import httpx
from src.modules.group_info import GroupInfo
from src.utils.config import config
from src.utils.user_agent import get_user_agent
from src.utils.utils import nickname

from .config import shuxing, zhiye


async def get_server(bot_id: int, group_id: int) -> str:
    '''
    获取绑定服务器名称
    '''
    return await GroupInfo.get_server(bot_id, group_id)


def get_daily_week(week: str) -> str:
    '''
    根据星期几返回额外的日常结果
    '''
    daily_list = {
        "一": "帮会跑商：阴山商路(10:00)\n阵营几天：出征祭祀(19:00)\n",
        "二": "阵营攻防：逐鹿中原(20:00)\n",
        "三": "世界首领：少林·乱世，七秀·乱世(20:00)\n",
        "四": "阵营攻防：逐鹿中原(20:00)\n",
        "五": "世界首领：藏剑·乱世，万花·乱世(20:00)\n",
        "六": "攻防前置：南屏山(12:00)\n阵营攻防：浩气盟(13:00，19:00)\n",
        "日": "攻防前置：昆仑(12:00)\n阵营攻防：恶人谷(13:00，19:00)\n"
    }
    return daily_list.get(week)


def hand_adventure_data(data: list[dict]) -> list[dict]:
    '''处理奇遇数据，转换时间'''
    for one_data in data:
        get_time = one_data.get('time')
        if get_time == 0:
            one_data['time'] = "未知"
        else:
            timeArray = time.localtime(get_time)
            one_data['time'] = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)

    return data


def _handle_attributes(attribute: dict) -> dict:
    '''预处理attribute'''
    data = {}
    data['score'] = attribute.get('score')
    data['totalLift'] = attribute.get('totalLift')
    data['atVitalityBase'] = attribute.get('atVitalityBase')
    data['atSpiritBase'] = attribute.get('atSpiritBase')
    data['atStrengthBase'] = attribute.get('atStrengthBase')
    data['atAgilityBase'] = attribute.get('atAgilityBase')
    data['atSpunkBase'] = attribute.get('atSpunkBase')
    data['totalAttack'] = attribute.get('totalAttack')
    data['baseAttack'] = attribute.get('baseAttack')
    data['totaltherapyPowerBase'] = attribute.get('totaltherapyPowerBase')
    data['therapyPowerBase'] = attribute.get('therapyPowerBase')
    data['atSurplusValueBase'] = attribute.get('atSurplusValueBase')
    # 会心
    data['atCriticalStrike'] = f"{attribute.get('atCriticalStrike')}（{attribute.get('atCriticalStrikeLevel')}%）"
    # 会效
    data['atCriticalDamagePowerBase'] = f"{attribute.get('atCriticalDamagePowerBase')}（{attribute.get('atCriticalDamagePowerBaseLevel')}%）"
    # 加速
    data['atHasteBase'] = f"{attribute.get('atHasteBaseLevel')}（{attribute.get('atHasteBase')}%）"
    # 破防
    data['atOvercome'] = f"{attribute.get('atOvercome')}（{attribute.get('atOvercomeBaseLevel')}%）"
    # 无双
    data['atStrainBase'] = f"{attribute.get('atStrainBase')}（{attribute.get('atStrainBaseLevel')}%）"
    # 外防
    data['atPhysicsShieldBase'] = f"{attribute.get('atPhysicsShieldBase')}（{attribute.get('atPhysicsShieldBaseLevel')}%）"
    # 内防
    data['atMagicShield'] = f"{attribute.get('atMagicShield')}（{attribute.get('atMagicShieldLevel')}%）"
    # 闪避
    data['atDodge'] = f"{attribute.get('atDodge')}（{attribute.get('atDodgeLevel')}%）"
    # 招架
    data['atParryBase'] = f"{attribute.get('atParryBase')}（{attribute.get('atParryBaseLevel')}%）"
    # 御劲
    data['atToughnessBase'] = f"{attribute.get('atToughnessBase')}（{attribute.get('atToughnessBaseLevel')}%）"
    # 化劲
    data['atDecriticalDamagePowerBase'] = f"{attribute.get('atDecriticalDamagePowerBase')}（{attribute.get('atDecriticalDamagePowerBaseLevel')}%）"

    return data


async def handle_data(alldata: dict) -> dict:
    '''预处理装备数据'''
    sectName = alldata.get("sectName")
    role = f'{alldata.get("forceName")}|{alldata.get("sectName")}'
    body = alldata.get("bodilyName")
    tittle = f'{alldata.get("serverName")}-{alldata.get("roleName")}'

    # 判断职业
    type_data = None
    for key, zhiye_data in zhiye.items():
        for one_data in zhiye_data:
            if one_data == sectName:
                type_data = key
                break
        if type_data is not None:
            break

    if type_data is None:
        type_data = "输出"

    shuxing_data = shuxing.get(type_data)
    num_data = alldata.get("data")
    attribute = num_data.get("attribute")
    post_equip = num_data.get('equip')
    post_qixue = num_data.get('qixue')

    attribute = _handle_attributes(attribute)
    post_attribute = _handle_data(role, body, attribute, shuxing_data)
    # 判断是否需要缓存
    img_cache: bool = config.get('default').get('img-cache')
    if img_cache:
        post_equip = await _handle_icon(post_equip)
        post_qixue = await _handle_icon(post_qixue)

    post_data = {}
    post_data['tittle'] = tittle
    post_data['nickname'] = nickname
    post_data['attribute'] = post_attribute
    post_data['equip'] = post_equip
    post_data['qixue'] = post_qixue

    return post_data


def _handle_data(role: str, body: str, attribute: dict, shuxing_data: dict) -> list:
    '''处理attribute数据'''
    data = []
    role_dict = {
        "tittle": "角色",
        "value": role
    }
    data.append(role_dict)
    body_dict = {
        "tittle": "体型",
        "value": body
    }
    data.append(body_dict)
    for key, value in shuxing_data.items():
        one_dict = {
            "tittle": value,
            "value": attribute.get(key)
        }
        data.append(one_dict)
    return data


async def _handle_icon(data: list[dict]) -> dict:
    '''处理icon'''
    html_path: str = config.get('path').get('html')
    icon_path = "."+html_path+"icons/"
    icons_files = os.listdir(icon_path)
    for one_data in data:
        icon_url = one_data.get('icon')
        icon_name = _get_icon_name(icon_url)
        filename = icon_path+icon_name
        if (icon_name in icons_files):
            # 文件已存在，替换url
            icon_file = "icons/"+icon_name
            one_data['icon'] = icon_file
        else:
            # 文件不存在，需要下载
            await _get_icon(icon_url, filename)

    return data


def _get_icon_name(url: str) -> str:
    '''从url返回文件名'''
    url_list = url.split("/")
    last = url_list[-1].split("?")
    return last[0]


async def _get_icon(url: str, filename: str) -> None:
    '''下载icon'''
    async with httpx.AsyncClient(headers=get_user_agent()) as client:
        req = await client.get(url)
        open(filename, 'wb').write(req.content)


def indicator_query_hanld(data: list[dict]) -> list[dict]:
    '''
    历史战绩预处理数据
    '''
    for one_data in data:
        get_time = one_data.get('start_time')
        timeArray = time.localtime(get_time)
        one_data['time'] = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)

    return data

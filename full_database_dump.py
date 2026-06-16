import json
import os
import re
import time
from datetime import datetime, timedelta, timezone
from html import unescape

import requests


EXTERNAL_SOURCES = [
    {
        "name": "球天下世界杯",
        "url": "https://m.qtx.com/worldcup",
        "kind": "schedule_news",
    },
    {
        "name": "7M赛前分析",
        "url": "https://news.7m.com.cn/list/5/index.shtml",
        "kind": "pre_match_news",
    },
    {
        "name": "7M AI模型预测",
        "url": "https://tv.7m.com.cn/big/",
        "kind": "ai_prediction",
    },
    {
        "name": "天天盈球",
        "url": "https://www.ttyingqiu.com/index",
        "kind": "score_news",
    },
    {
        "name": "天天盈球世界杯积分",
        "url": "https://www.ttyingqiu.com/live/zq/league/1999/tab/jf?season=2026",
        "kind": "standings",
    },
]


def flag(code):
    return f"https://flagsapi.com/{code}/flat/32.png" if code else ""


TEAM_STRENGTH = {
    "法國": 88, "塞內加爾": 78, "伊拉克": 62, "挪威": 79,
    "阿根廷": 91, "阿爾及利亞": 73, "奧地利": 76, "約旦": 61,
    "迦納": 72, "巴拿馬": 64, "英格蘭": 87, "克羅埃西亞": 80,
    "葡萄牙": 86, "剛果民主共和國": 67, "烏茲別克": 66, "哥倫比亞": 79,
    "捷克": 74, "南非": 63, "瑞士": 79, "波士尼亞": 70,
    "加拿大": 72, "卡達": 65, "墨西哥": 76, "韓國": 74,
}

TEAM_ALIASES = {
    "法國": ["法國", "法国", "France"],
    "塞內加爾": ["塞內加爾", "塞内加尔", "Senegal"],
    "伊拉克": ["伊拉克", "Iraq"],
    "挪威": ["挪威", "Norway"],
    "阿根廷": ["阿根廷", "Argentina"],
    "阿爾及利亞": ["阿爾及利亞", "阿尔及利亚", "Algeria"],
    "奧地利": ["奧地利", "奥地利", "Austria"],
    "約旦": ["約旦", "约旦", "Jordan"],
    "迦納": ["迦納", "加纳", "Ghana"],
    "巴拿馬": ["巴拿馬", "巴拿马", "Panama"],
    "英格蘭": ["英格蘭", "英格兰", "England"],
    "克羅埃西亞": ["克羅埃西亞", "克罗地亚", "Croatia"],
    "葡萄牙": ["葡萄牙", "Portugal"],
    "剛果民主共和國": ["剛果民主共和國", "刚果民主共和国", "民主刚果", "Congo DR"],
    "烏茲別克": ["烏茲別克", "乌兹别克", "Uzbekistan"],
    "哥倫比亞": ["哥倫比亞", "哥伦比亚", "Colombia"],
    "捷克": ["捷克", "Czech"],
    "南非": ["南非", "South Africa"],
    "瑞士": ["瑞士", "Switzerland"],
    "波士尼亞": ["波士尼亞", "波黑", "Bosnia"],
    "加拿大": ["加拿大", "Canada"],
    "卡達": ["卡達", "卡塔尔", "Qatar"],
    "墨西哥": ["墨西哥", "Mexico"],
    "韓國": ["韓國", "韩国", "Korea"],
}


TAIPEI_TZ = timezone(timedelta(hours=8))


def kickoff_label(date, label):
    if label and re.search(r"\d{1,2}:\d{2}", label):
        return label
    try:
        kickoff = datetime.fromisoformat(date).astimezone(TAIPEI_TZ)
        return kickoff.strftime("%Y/%m/%d %H:%M")
    except ValueError:
        return label


def game(home, away, home_flag, away_flag, date, label, venue, round_, status="\u672a\u958b\u8cfd"):
    return {
        "home": home,
        "away": away,
        "homeFlag": flag(home_flag),
        "awayFlag": flag(away_flag),
        "date": date,
        "time": kickoff_label(date, label),
        "venue": venue,
        "round": round_,
        "status": status,
    }


SCHEDULE_GAMES = [
    game("法國", "塞內加爾", "FR", "SN", "2026-06-16T15:00:00-04:00", "2026/06/17 03:00", "紐約/紐澤西", "I組", "今日賽事"),
    game("伊拉克", "挪威", "IQ", "NO", "2026-06-16T00:00:00-04:00", "2026/06/16", "波士頓", "I組", "今日賽事"),
    game("阿根廷", "阿爾及利亞", "AR", "DZ", "2026-06-16T00:00:00-05:00", "2026/06/16", "堪薩斯城", "J組", "今日賽事"),
    game("奧地利", "約旦", "AT", "JO", "2026-06-16T00:00:00-07:00", "2026/06/16", "舊金山灣區", "J組", "今日賽事"),
    game("迦納", "巴拿馬", "GH", "PA", "2026-06-17T00:00:00-04:00", "2026/06/17", "多倫多", "L組"),
    game("英格蘭", "克羅埃西亞", "GB", "HR", "2026-06-17T00:00:00-05:00", "2026/06/17", "達拉斯", "L組"),
    game("葡萄牙", "剛果民主共和國", "PT", "CD", "2026-06-17T00:00:00-05:00", "2026/06/17", "休士頓", "K組"),
    game("烏茲別克", "哥倫比亞", "UZ", "CO", "2026-06-17T00:00:00-06:00", "2026/06/17", "墨西哥城", "K組"),
    game("捷克", "南非", "CZ", "ZA", "2026-06-18T00:00:00-04:00", "2026/06/18", "亞特蘭大", "A組"),
    game("瑞士", "波士尼亞", "CH", "BA", "2026-06-18T00:00:00-07:00", "2026/06/18", "洛杉磯", "B組"),
    game("加拿大", "卡達", "CA", "QA", "2026-06-18T00:00:00-07:00", "2026/06/18", "溫哥華", "B組"),
    game("墨西哥", "韓國", "MX", "KR", "2026-06-18T00:00:00-06:00", "2026/06/18", "瓜達拉哈拉", "A組"),
]


def clamp(value, low, high):
    return max(low, min(high, value))


def stable_hash(text):
    h = 0
    for ch in text:
        h = ((h << 5) - h + ord(ch)) & 0xFFFFFFFF
    return h


def build_recommendation_panel(home, away, home_rate, away_rate, predicted_score, expected_goals, over25, btts, model_score):
    favorite = home if home_rate >= away_rate else away
    underdog = away if home_rate >= away_rate else home
    edge = abs(home_rate - away_rate)
    total_line = "大 2.5" if over25 >= 58 else "小 2.5" if over25 <= 48 else "2/2.5 觀察"
    goal_count = "2-4 球" if expected_goals >= 2.75 else "1-2 球" if expected_goals <= 2.25 else "2-3 球"
    handicap = f"{favorite} -0.5" if edge >= 18 else f"{underdog} +0.5 受讓"
    first_half = "特1：上半場有球" if expected_goals >= 2.75 else "特1：上半場小 1"
    return [
        {"key": "score", "label": "比分", "value": predicted_score, "confidence": model_score},
        {"key": "total", "label": "大小球", "value": total_line, "confidence": over25 if over25 >= 58 else 100 - over25},
        {"key": "handicap", "label": "讓球/受讓", "value": handicap, "confidence": 68 if edge >= 18 else 58},
        {"key": "winRate", "label": "勝率方向", "value": f"{favorite} {max(home_rate, away_rate)}%", "confidence": max(home_rate, away_rate)},
        {"key": "goalCount", "label": "進球數", "value": goal_count, "confidence": round(expected_goals * 22)},
        {"key": "firstHalf", "label": "特1/半場", "value": first_half, "confidence": 61 if expected_goals >= 2.75 else 56},
        {"key": "btts", "label": "雙方進球", "value": "是" if btts >= 58 else "觀察", "confidence": btts},
    ]


def predict_score(home_rate, away_rate, expected_goals, btts, upset, seed):
    edge = abs(home_rate - away_rate)
    home_share = home_rate / max(1, home_rate + away_rate)
    home_xg = expected_goals * (0.42 + home_share * 0.38)
    away_xg = expected_goals - home_xg

    home_xg += ((seed % 5) - 2) * 0.08
    away_xg += (((seed >> 3) % 5) - 2) * 0.08

    home_goals = clamp(round(home_xg), 0, 4)
    away_goals = clamp(round(away_xg), 0, 4)

    if edge >= 28:
        if home_rate > away_rate:
            home_goals = max(home_goals, away_goals + (2 if expected_goals >= 3 else 1))
        else:
            away_goals = max(away_goals, home_goals + (2 if expected_goals >= 3 else 1))
    elif edge <= 8 and btts >= 56:
        home_goals = max(1, home_goals)
        away_goals = max(1, away_goals)

    if expected_goals < 2.25 and home_goals + away_goals > 2:
        if home_goals >= away_goals:
            home_goals -= 1
        else:
            away_goals -= 1
    elif expected_goals >= 3.05 and home_goals + away_goals < 3:
        if home_rate >= away_rate:
            home_goals += 1
        else:
            away_goals += 1

    if btts < 48 and edge >= 14:
        concede = 1 if seed % 3 == 0 or upset > 60 else 0
        if home_rate >= away_rate:
            away_goals = min(away_goals, concede)
        else:
            home_goals = min(home_goals, concede)

    home_goals = clamp(home_goals, 0, 4)
    away_goals = clamp(away_goals, 0, 4)

    if home_goals == 0 and away_goals == 0 and expected_goals >= 2.15:
        if home_rate >= away_rate:
            home_goals = 1
        else:
            away_goals = 1

    return f"{home_goals}-{away_goals}"


def team_tier(strength):
    if strength >= 86:
        return {"label": "頂級強隊", "attack": 1.16, "defense": 0.78, "volatility": 0.82}
    if strength >= 78:
        return {"label": "強隊", "attack": 1.08, "defense": 0.88, "volatility": 0.92}
    if strength >= 70:
        return {"label": "中上隊", "attack": 1.00, "defense": 1.00, "volatility": 1.00}
    if strength >= 62:
        return {"label": "中段隊", "attack": 0.90, "defense": 1.12, "volatility": 1.10}
    return {"label": "弱隊", "attack": 0.78, "defense": 1.28, "volatility": 1.22}


def predict_score_with_team_tiers(home_strength, away_strength, home_rate, away_rate, expected_goals, btts, upset, seed):
    home_tier = team_tier(home_strength)
    away_tier = team_tier(away_strength)
    strength_gap = home_strength - away_strength
    abs_gap = abs(strength_gap)
    home_share = home_rate / max(1, home_rate + away_rate)

    home_xg = expected_goals * (0.40 + home_share * 0.40)
    away_xg = expected_goals - home_xg
    home_xg *= home_tier["attack"] * away_tier["defense"]
    away_xg *= away_tier["attack"] * home_tier["defense"]

    if abs_gap >= 18:
        if strength_gap > 0:
            home_xg += 0.28
            away_xg -= 0.18
        else:
            away_xg += 0.28
            home_xg -= 0.18

    volatility = (home_tier["volatility"] + away_tier["volatility"]) / 2
    home_xg += ((seed % 7) - 3) * 0.045 * volatility
    away_xg += (((seed >> 4) % 7) - 3) * 0.045 * volatility

    if upset >= 60:
        if home_rate >= away_rate:
            away_xg += 0.16
        else:
            home_xg += 0.16

    home_xg = clamp(home_xg, 0.12, 3.8)
    away_xg = clamp(away_xg, 0.12, 3.8)
    home_goals = clamp(round(home_xg), 0, 4)
    away_goals = clamp(round(away_xg), 0, 4)

    if abs_gap >= 24:
        if strength_gap > 0:
            home_goals = max(home_goals, away_goals + 1)
            if expected_goals >= 3 or home_xg >= 2.15:
                home_goals = max(home_goals, 2)
            if btts < 58:
                away_goals = min(away_goals, 1 if upset >= 62 else 0)
        else:
            away_goals = max(away_goals, home_goals + 1)
            if expected_goals >= 3 or away_xg >= 2.15:
                away_goals = max(away_goals, 2)
            if btts < 58:
                home_goals = min(home_goals, 1 if upset >= 62 else 0)
    elif abs_gap <= 8 and btts >= 56:
        home_goals = max(1, home_goals)
        away_goals = max(1, away_goals)

    if expected_goals < 2.25 and home_goals + away_goals > 2:
        if home_goals > away_goals:
            home_goals -= 1
        elif away_goals > home_goals:
            away_goals -= 1
        elif seed % 2 == 0:
            home_goals -= 1
        else:
            away_goals -= 1

    if expected_goals >= 3.05 and home_goals + away_goals < 3:
        if home_xg >= away_xg:
            home_goals += 1
        else:
            away_goals += 1

    if home_goals == 0 and away_goals == 0 and expected_goals >= 2.05:
        if home_xg >= away_xg:
            home_goals = 1
        else:
            away_goals = 1

    return {
        "score": f"{clamp(home_goals, 0, 4)}-{clamp(away_goals, 0, 4)}",
        "homeTier": home_tier["label"],
        "awayTier": away_tier["label"],
        "homeXg": round(home_xg, 2),
        "awayXg": round(away_xg, 2),
        "strengthGap": strength_gap,
    }


def clean_text(text):
    text = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def fetch_html(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; FootballDataBot/1.0; +https://my-best-football.vercel.app)",
        "Accept": "text/html,application/xhtml+xml",
    }
    res = requests.get(url, headers=headers, timeout=15)
    res.raise_for_status()
    if not res.encoding or res.encoding.lower() in ("iso-8859-1", "ascii"):
        res.encoding = res.apparent_encoding or "utf-8"
    return res.text


def extract_qtx(html):
    text = clean_text(html)
    matches = []
    pattern = re.compile(r"世界杯\s+(未开赛|进行中|完场)\s+([^\s]+)\s+([^\s]+)\s+(\d{2}-\d{2}\s+\d{2}:\d{2})")
    for status, home, away, kickoff in pattern.findall(text):
        matches.append({
            "home": home,
            "away": away,
            "time": kickoff,
            "status": status,
            "source": "球天下世界杯",
        })

    titles = []
    for title in re.findall(r"(2026世界杯[^。；\n]{8,80})", text):
        if title not in titles:
            titles.append(title)
    return {"matches": matches[:12], "headlines": titles[:12]}


def extract_7m(html):
    text = clean_text(html)
    titles = []
    keywords = ("世界", "盃", "杯", "分析", "推介", "赛前", "賽前")
    for part in re.split(r"\s{2,}|上一篇|下一篇", text):
        part = part.strip(" -_|")
        if 8 <= len(part) <= 80 and any(k in part for k in keywords):
            if part not in titles:
                titles.append(part)
    return {"matches": [], "headlines": titles[:12]}


def pct(value, fallback=""):
    text = str(value or "").strip()
    return text or fallback


def ai_side(value, home, away):
    if value == 1:
        return home
    if value == 2:
        return "和局"
    if value == 3:
        return away
    return "觀察"


def extract_7m_ai(html):
    ids = []
    for match_id in re.findall(r"ShowAnalyse_big\((\d+)\)", html):
        if match_id not in ids:
            ids.append(match_id)

    matches = []
    headlines = []
    for match_id in ids[:8]:
        try:
            raw = fetch_html(f"https://txt-api.7mdt.com/specials/worldcup2026/getMatchAiData?matchId={match_id}&lan=3&t={int(time.time())}")
            payload = json.loads(raw)
            data = payload.get("data") or {}
            match = data.get("match") or {}
            home = match.get("homeName") or ""
            away = match.get("awayName") or ""
            if not home or not away:
                continue
            score = ((data.get("score") or {}).get("options") or [{}])[0]
            goal = ((data.get("goal") or {}).get("options") or [{}])[0]
            wdl = data.get("wdl") or {}
            overunder = data.get("overunder") or {}
            handicap = data.get("handicap") or {}
            total_pick = "大" if overunder.get("predict") == 1 else "小" if overunder.get("predict") == 2 else "觀察"
            handicap_pick = home if handicap.get("predict") == 1 else away if handicap.get("predict") == 2 else "觀察"
            line = handicap.get("handicap", "")
            summary = (
                f"{home} vs {away}｜比分{score.get('score', '觀察')}｜"
                f"大小{total_pick}{overunder.get('score', '')}｜"
                f"讓球{handicap_pick} {line}｜"
                f"勝率{ai_side(wdl.get('predict'), home, away)}｜"
                f"進球數{goal.get('score', '觀察')}"
            )
            matches.append({
                "home": home,
                "away": away,
                "time": "",
                "status": "7M AI",
                "source": "7M AI模型预测",
                "matchId": match_id,
                "summary": summary,
            })
            headlines.append(summary)
        except Exception:
            continue
    return {"matches": matches, "headlines": headlines}


def extract_ttyingqiu(html):
    text = clean_text(html)
    titles = []
    for marker in ("头条资讯", "赛事资讯"):
        if marker in text:
            text = text[text.find(marker):]
            break
    for part in re.split(r"·\s*\d+分钟前|更多|足球比分|篮球比分", text):
        part = part.strip(" -_|")
        if 10 <= len(part) <= 90 and not part.startswith("下载"):
            if part not in titles:
                titles.append(part)
    return {"matches": [], "headlines": titles[:8]}


def extract_ttyingqiu_standings(html):
    text = clean_text(html)
    titles = []
    for key in ("2026赛季世界杯积分榜", "世界杯积分榜", "世界杯排名"):
        if key in text:
            titles.append("天天盈球2026世界盃積分頁已連線，可作分組積分來源。")
            break
    if not titles:
        titles.append("天天盈球世界盃積分頁可連線，但實際表格可能由前端動態載入。")
    return {"matches": [], "headlines": titles[:3]}


def worldcup_group_standings():
    def row(rank, flag_code, team, played=0, wins=0, draws=0, losses=0, gf=0, ga=0):
        return {"rank": rank, "flag": flag(flag_code), "team": team, "played": played, "wins": wins, "draws": draws, "losses": losses, "gf": gf, "ga": ga, "gd": gf - ga, "pts": wins * 3 + draws}

    source_groups = [
        ("A", [("MX", "\u58a8\u897f\u54e5", 1, 1, 0, 0, 2, 0), ("KR", "\u97d3\u570b", 1, 1, 0, 0, 2, 1), ("CZ", "\u6377\u514b", 1, 0, 0, 1, 1, 2), ("ZA", "\u5357\u975e", 1, 0, 0, 1, 0, 2)]),
        ("B", [("CH", "\u745e\u58eb", 1, 0, 1, 0, 1, 1), ("CA", "\u52a0\u62ff\u5927", 1, 0, 1, 0, 1, 1), ("QA", "\u5361\u9054", 1, 0, 1, 0, 1, 1), ("BA", "\u6ce2\u58eb\u5c3c\u4e9e", 1, 0, 1, 0, 1, 1)]),
        ("C", [("GB-SCT", "\u8607\u683c\u862d", 1, 1, 0, 0, 1, 0), ("MA", "\u6469\u6d1b\u54e5", 1, 0, 1, 0, 1, 1), ("BR", "\u5df4\u897f", 1, 0, 1, 0, 1, 1), ("HT", "\u6d77\u5730", 1, 0, 0, 1, 0, 1)]),
        ("D", [("US", "\u7f8e\u570b", 1, 1, 0, 0, 4, 1), ("AU", "\u6fb3\u5927\u5229\u4e9e", 1, 1, 0, 0, 2, 0), ("TR", "\u571f\u8033\u5176", 1, 0, 0, 1, 0, 2), ("PY", "\u5df4\u62c9\u572d", 1, 0, 0, 1, 1, 4)]),
        ("E", [("DE", "\u5fb7\u570b", 1, 1, 0, 0, 7, 1), ("CI", "\u79d1\u7279\u8fea\u74e6", 1, 1, 0, 0, 1, 0), ("EC", "\u5384\u74dc\u591a\u723e", 1, 0, 0, 1, 0, 1), ("CW", "\u5eab\u62c9\u7d22", 1, 0, 0, 1, 1, 7)]),
        ("F", [("SE", "\u745e\u5178", 1, 1, 0, 0, 5, 1), ("JP", "\u65e5\u672c", 1, 0, 1, 0, 2, 2), ("NL", "\u8377\u862d", 1, 0, 1, 0, 2, 2), ("TN", "\u7a81\u5c3c\u897f\u4e9e", 1, 0, 0, 1, 1, 5)]),
        ("G", [("NZ", "\u7d10\u897f\u862d", 1, 0, 1, 0, 2, 2), ("IR", "\u4f0a\u6717", 1, 0, 1, 0, 2, 2), ("BE", "\u6bd4\u5229\u6642", 1, 0, 1, 0, 1, 1), ("EG", "\u57c3\u53ca", 1, 0, 1, 0, 1, 1)]),
        ("H", [("UY", "\u70cf\u62c9\u572d", 1, 0, 1, 0, 1, 1), ("SA", "\u6c99\u70cf\u5730\u963f\u62c9\u4f2f", 1, 0, 1, 0, 1, 1), ("ES", "\u897f\u73ed\u7259", 1, 0, 1, 0, 0, 0), ("CV", "\u7dad\u5fb7\u89d2", 1, 0, 1, 0, 0, 0)]),
        ("I", [("FR", "\u6cd5\u570b"), ("SN", "\u585e\u5167\u52a0\u723e"), ("NO", "\u632a\u5a01"), ("IQ", "\u4f0a\u62c9\u514b")]),
        ("J", [("AR", "\u963f\u6839\u5ef7"), ("AT", "\u5967\u5730\u5229"), ("DZ", "\u963f\u723e\u53ca\u5229\u4e9e"), ("JO", "\u7d04\u65e6")]),
        ("K", [("PT", "\u8461\u8404\u7259"), ("CO", "\u54e5\u502b\u6bd4\u4e9e"), ("UZ", "\u70cf\u8332\u5225\u514b"), ("CD", "\u525b\u679c\u6c11\u4e3b\u5171\u548c\u570b")]),
        ("L", [("GB-ENG", "\u82f1\u683c\u862d"), ("HR", "\u514b\u7f85\u57c3\u897f\u4e9e"), ("GH", "\u8fe6\u7d0d"), ("PA", "\u5df4\u62ff\u99ac")]),
    ]
    groups = []
    for group_key, teams in source_groups:
        group_rows = [row(rank, *team) for rank, team in enumerate(teams, 1)]
        groups.append({"group": f"{group_key}\u7d44", "sourceGroup": group_key, "teams": group_rows})
    third_place = []
    for group in groups:
        team = dict(group["teams"][2])
        team["group"] = group["group"]
        third_place.append(team)
    third_place.sort(key=lambda team: (-team["pts"], -team["gd"], -team["gf"], team["ga"], team["group"]))
    for index, team in enumerate(third_place, 1):
        team["rank"] = index
        team["team"] = f"{team['team']} ({team['group']})"
    groups.append({"group": "\u7b2c3\u540d\u968a\u4f0d\u6392\u540d", "sourceGroup": "\u7b2c3\u540d\u961f\u4f0d\u6392\u540d", "type": "thirdPlace", "teams": third_place})
    return {"source": "ttyingqiu-standings-cache", "sourceUrl": "https://www.ttyingqiu.com/live/zq/league/1999/tab/jf?season=2026", "updatedAt": time.strftime("%Y-%m-%d %H:%M:%S"), "groups": groups}

def collect_external_intel():
    extractors = {
        "球天下世界杯": extract_qtx,
        "7M赛前分析": extract_7m,
        "7M AI模型预测": extract_7m_ai,
        "天天盈球": extract_ttyingqiu,
        "天天盈球世界杯积分": extract_ttyingqiu_standings,
    }
    results = []
    for source in EXTERNAL_SOURCES:
        item = {
            "name": source["name"],
            "url": source["url"],
            "kind": source["kind"],
            "ok": False,
            "matches": [],
            "headlines": [],
            "error": "",
        }
        try:
            parsed = extractors[source["name"]](fetch_html(source["url"]))
            item.update(parsed)
            item["ok"] = True
        except Exception as exc:
            item["error"] = str(exc)[:180]
        results.append(item)
    return results


def aliases_for(team_name):
    return TEAM_ALIASES.get(team_name, [team_name])


def related_external_notes(game_item, external_intel):
    home_aliases = aliases_for(game_item["home"])
    away_aliases = aliases_for(game_item["away"])
    notes = []
    for source in external_intel:
        for match in source.get("matches", []):
            text = f"{match.get('home', '')} {match.get('away', '')}"
            if any(a in text for a in home_aliases) and any(a in text for a in away_aliases):
                notes.append(f"{source['name']}賽程：{match.get('home')} vs {match.get('away')}｜{match.get('time')}｜{match.get('status')}")
        for title in source.get("headlines", []):
            if any(a in title for a in home_aliases + away_aliases):
                notes.append(f"{source['name']}：{title}")
    return notes[:4]


def form(seed, strength):
    wins = clamp(round(strength / 14 + seed % 4 - 2), 2, 10)
    draws = clamp(4 + seed % 3 - 1, 2, 6)
    losses = 15 - wins - draws
    goals_for = clamp(round(wins * 1.8 + draws * 0.8 + seed % 5), 8, 32)
    goals_against = clamp(round(losses * 1.5 + draws * 0.7 + seed % 4), 5, 25)
    return {
        "wins": wins, "draws": draws, "losses": losses,
        "points": wins * 3 + draws,
        "goalsFor": goals_for, "goalsAgainst": goals_against,
        "avgGoalsFor": round(goals_for / 15, 2),
        "avgGoalsAgainst": round(goals_against / 15, 2),
        "score": round(strength / 100, 2),
        "totalGames": 15,
        "recentResults": [],
    }


def analyze_game(g, external_intel=None):
    external_intel = external_intel or []
    home_strength = TEAM_STRENGTH.get(g["home"], 68)
    away_strength = TEAM_STRENGTH.get(g["away"], 68)
    seed = stable_hash(g["home"] + ":" + g["away"])
    diff = home_strength - away_strength
    home_rate = clamp(round(50 + diff * 0.9 + (seed % 9) - 4), 18, 82)
    away_rate = 100 - home_rate
    favorite = g["home"] if home_rate >= away_rate else g["away"]
    model_score = clamp(round(max(home_rate, away_rate) + abs(diff) * 0.25), 45, 92)
    expected_goals = round(clamp(2.15 + abs(diff) / 45 + (seed % 7) / 20, 1.8, 3.7), 2)
    over25 = clamp(round(46 + expected_goals * 8 + seed % 8), 42, 78)
    btts = clamp(round(42 + (100 - abs(diff)) / 5 + seed % 7), 38, 72)
    upset = clamp(round(62 - abs(diff) * 0.55 + seed % 9), 28, 68)
    score_model = predict_score_with_team_tiers(
        home_strength, away_strength, home_rate, away_rate,
        expected_goals, btts, upset, seed
    )
    predicted_score = score_model["score"]

    item = dict(g)
    external_notes = related_external_notes(g, external_intel)
    item.update({
        "fixtureId": None,
        "homeRate": home_rate,
        "awayRate": away_rate,
        "predictedWinner": favorite,
        "predictedScore": predicted_score,
        "recommendationPanel": build_recommendation_panel(
            g["home"], g["away"], home_rate, away_rate, predicted_score,
            expected_goals, over25, btts, model_score
        ),
        "recommendation": f"{favorite} 優勢觀察" if abs(home_rate - away_rate) >= 12 else "雙方接近，重點觀察開局節奏",
        "confidence": "中高" if model_score >= 70 else "中",
        "stars": "⭐⭐⭐⭐" if model_score >= 70 else "⭐⭐⭐",
        "diff": abs(home_rate - away_rate),
        "goalModel": {
            "expectedGoals": expected_goals,
            "homeExpectedGoals": score_model["homeXg"],
            "awayExpectedGoals": score_model["awayXg"],
            "over25": over25,
            "under25": 100 - over25,
            "btts": btts,
            "totalLean": "偏高進球" if over25 >= 60 else "均衡",
        },
        "teamTierModel": {
            "homeTier": score_model["homeTier"],
            "awayTier": score_model["awayTier"],
            "strengthGap": score_model["strengthGap"],
            "note": "比分已加入隊伍強弱分層、攻防係數、弱隊失球風險與爆冷變數。",
        },
        "upsetModel": {
            "upsetIndex": upset,
            "label": "冷門風險" if upset >= 58 else "變數觀察",
            "reason": "本模型使用站內世界盃賽程與球隊基礎強度估算，不依賴外部 Render 分析後端。",
        },
        "tags": ["🏆 世界盃", "📅 最新賽程", "🧠 本地模型"],
        "market": "外部公開資訊：" + "；".join(external_notes[:2]) if external_notes else "站內自建資料模型；外部公開資料暫無直接命中。",
        "externalIntel": external_notes,
        "qualityScore": model_score,
        "homeForm": form(seed, home_strength),
        "awayForm": form(seed >> 2, away_strength),
    })
    return item


def build_database():
    external_intel = collect_external_intel()
    recommended = [analyze_game(g, external_intel) for g in SCHEDULE_GAMES[:8]]
    return {
        "metadata": {
            "source": "site-local-worldcup-model",
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "auth_used": "none",
            "external_sources": [
                {"name": item["name"], "url": item["url"], "ok": item["ok"], "error": item["error"]}
                for item in external_intel
            ],
        },
        "endpoints": {
            "schedule": {
                "date": "2026-06-16",
                "source": "site-local-worldcup-model",
                "stageLabel": "小組賽進行中",
                "nextGame": SCHEDULE_GAMES[0],
                "scheduleGames": SCHEDULE_GAMES,
            },
            "recommended": {
                "date": "2026-06-16",
                "source": "site-local-worldcup-model",
                "strongSignals": recommended[:3],
                "defenseSignals": recommended[3:5],
                "goalSignals": recommended[:4],
                "upsetSignals": recommended[4:8],
                "splitSignals": [],
            },
            "groupStandings": worldcup_group_standings(),
            "analyses": recommended,
            "externalIntel": external_intel,
        },
    }


def scrape_all_data():
    folder = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(folder, "FOOTBALL_FULL_DATABASE_DUMP.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(build_database(), f, ensure_ascii=False, indent=2)
    print(f"LOCAL FOOTBALL DATABASE SAVED TO: {output_path}")


if __name__ == "__main__":
    scrape_all_data()

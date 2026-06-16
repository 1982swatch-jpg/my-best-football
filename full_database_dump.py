import json
import os
import re
import time
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


def game(home, away, home_flag, away_flag, date, label, venue, round_, status="未開賽"):
    return {
        "home": home,
        "away": away,
        "homeFlag": flag(home_flag),
        "awayFlag": flag(away_flag),
        "date": date,
        "time": label,
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
    predicted_score = "2-1" if abs(diff) > 8 else "1-1"

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
            "over25": over25,
            "under25": 100 - over25,
            "btts": btts,
            "totalLean": "偏高進球" if over25 >= 60 else "均衡",
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

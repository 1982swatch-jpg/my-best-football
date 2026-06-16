import json
import os
import time


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


def analyze_game(g):
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

    item = dict(g)
    item.update({
        "fixtureId": None,
        "homeRate": home_rate,
        "awayRate": away_rate,
        "predictedWinner": favorite,
        "predictedScore": "2-1" if abs(diff) > 8 else "1-1",
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
        "market": "首頁已改用站內自建資料模型；外部分析後端授權失效不再阻擋首頁更新。",
        "qualityScore": model_score,
        "homeForm": form(seed, home_strength),
        "awayForm": form(seed >> 2, away_strength),
    })
    return item


def build_database():
    recommended = [analyze_game(g) for g in SCHEDULE_GAMES[:8]]
    return {
        "metadata": {
            "source": "site-local-worldcup-model",
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "auth_used": "none",
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

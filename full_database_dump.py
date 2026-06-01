import requests
from requests.auth import HTTPBasicAuth
import json
import time
import os

base_url = "https://football-analyzer-briu.onrender.com"
auth = HTTPBasicAuth('worldcup', '2026')

def scrape_all_data():
    # Use relative path
    folder = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(folder, "FOOTBALL_FULL_DATABASE_DUMP.json")

    master_db = {
        "metadata": {
            "source": base_url,
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "auth_used": "Basic Auth"
        },
        "endpoints": {
            "schedule": None,
            "recommended": None,
            "analyses": []
        }
    }

    # 1. Scrape Schedule
    print("Fetching /schedule...")
    res = requests.get(base_url + "/schedule", auth=auth)
    if res.status_code == 200:
        master_db["endpoints"]["schedule"] = res.json()
    
    # 2. Scrape Recommended
    print("Fetching /recommended...")
    res = requests.get(base_url + "/recommended", auth=auth)
    if res.status_code == 200:
        master_db["endpoints"]["recommended"] = res.json()

    # 3. Scrape Detailed Analysis
    match_pairs = []
    if master_db["endpoints"]["schedule"]:
        games = master_db["endpoints"]["schedule"].get("scheduleGames", [])
        for g in games:
            match_pairs.append((g.get("home"), g.get("away"), g.get("fixtureId", "")))
    if master_db["endpoints"]["recommended"]:
        reco = master_db["endpoints"]["recommended"]
        for key in ["strongSignals", "defenseSignals", "goalSignals", "upsetSignals", "splitSignals"]:
            if key in reco:
                for g in reco[key]:
                    match_pairs.append((g.get("home"), g.get("away"), g.get("fixtureId", "")))

    unique_pairs = list(set(match_pairs))
    print(f"Found {len(unique_pairs)} unique matches to analyze.")

    for home, away, fixture in unique_pairs:
        if not home or not away: continue
        print(f"Analyzing: {home} vs {away}...")
        url = f"{base_url}/analyze?home={home}&away={away}&fixture={fixture}"
        try:
            res = requests.get(url, auth=auth)
            if res.status_code == 200:
                master_db["endpoints"]["analyses"].append(res.json())
        except Exception as e:
            print(f"  Error: {e}")
        time.sleep(0.5)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(master_db, f, ensure_ascii=False, indent=2)
    
    print(f"\nFULL DATABASE DUMP SAVED TO: {output_path}")

if __name__ == "__main__":
    scrape_all_data()

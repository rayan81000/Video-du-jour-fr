"""Met à jour data.json avec les vidéos françaises du jour (tendances YouTube France), puis régénère la page.
Clé API lue dans la variable d'environnement YOUTUBE_API_KEY."""
import json, os, subprocess, sys, urllib.parse, urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

API = "https://www.googleapis.com/youtube/v3/"
MAX_AGE_HOURS = 24
HERE = os.path.dirname(os.path.abspath(__file__))
CATEGORIES = {"10": "Musique", "20": "Jeux", "1": "Cinéma", "30": "Cinéma", "44": "Cinéma"}


def call(endpoint, **params):
    params["key"] = os.environ["YOUTUBE_API_KEY"]
    with urllib.request.urlopen(API + endpoint + "?" + urllib.parse.urlencode(params), timeout=30) as r:
        return json.load(r)


def is_french(sn):
    lang = (sn.get("defaultAudioLanguage") or sn.get("defaultLanguage") or "").lower()
    return lang == "" or lang.startswith("fr")


def main():
    if not os.environ.get("YOUTUBE_API_KEY"):
        sys.exit("Variable YOUTUBE_API_KEY manquante.")
    now = datetime.now(timezone.utc)
    items, token = [], None
    for _ in range(3):
        p = dict(part="snippet,statistics", chart="mostPopular", regionCode="FR", maxResults=50, hl="fr")
        if token:
            p["pageToken"] = token
        d = call("videos", **p)
        items += d.get("items", [])
        token = d.get("nextPageToken")
        if not token:
            break
    keep = []
    for it in items:
        sn = it["snippet"]
        hours = (now - datetime.fromisoformat(sn["publishedAt"].replace("Z", "+00:00"))).total_seconds() / 3600
        if hours <= MAX_AGE_HOURS and is_french(sn):
            keep.append((it, hours))
    if not keep:
        sys.exit("Aucune vidéo trouvée : fichiers conservés.")
    # Nombre d'abonnés des chaînes (pour repérer les grands YouTubeurs)
    ids = sorted({it["snippet"]["channelId"] for it, _ in keep})
    subs = {}
    for i in range(0, len(ids), 50):
        d = call("channels", part="statistics", id=",".join(ids[i:i + 50]))
        for c in d.get("items", []):
            subs[c["id"]] = int(c["statistics"].get("subscriberCount", 0))
    videos = [{
        "title": it["snippet"]["title"], "channel": it["snippet"]["channelTitle"], "id": it["id"],
        "views": int(it.get("statistics", {}).get("viewCount", 0)), "hours": max(1, round(h)),
        "category": CATEGORIES.get(it["snippet"].get("categoryId"), "Divers"),
        "subs": subs.get(it["snippet"]["channelId"], 0),
    } for it, h in keep]
    videos.sort(key=lambda v: v["views"], reverse=True)
    with open(os.path.join(HERE, "data.json"), "w", encoding="utf-8") as f:
        json.dump({"generated": now.astimezone(ZoneInfo("Europe/Paris")).isoformat(timespec="seconds"),
                   "videos": videos}, f, ensure_ascii=False, indent=1)
    subprocess.run([sys.executable, os.path.join(HERE, "build.py")], check=True)


if __name__ == "__main__":
    main()

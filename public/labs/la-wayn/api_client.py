"""OpenStreetMap restaurant discovery through the public Overpass API."""
import json
import math
import urllib.parse
import urllib.request

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def search_restaurants(lat, lon, radius_m, cuisines=None, vegetarian=False, halal=False, open_now=False, weekday=None, minute_of_day=None, timeout=25):
    """Return restaurants within radius, with normalized OSM tags and coordinates."""
    query = f"""[out:json][timeout:20];
    (node[amenity~\"^(restaurant|fast_food|cafe|food_court)$\"](around:{radius_m},{lat},{lon});
     way[amenity~\"^(restaurant|fast_food|cafe|food_court)$\"](around:{radius_m},{lat},{lon});
     relation[amenity~\"^(restaurant|fast_food|cafe|food_court)$\"](around:{radius_m},{lat},{lon}););
    out center tags;"""
    request = urllib.request.Request(OVERPASS_URL, data=urllib.parse.urlencode({"data": query}).encode(), headers={"User-Agent": "LaWaynMVP/1.0 (restaurant discovery)", "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    wanted = {item.lower() for item in (cuisines or [])}
    found, seen = [], set()
    for element in payload.get("elements", []):
        tags = element.get("tags", {})
        name = tags.get("name")
        if not name:
            continue
        raw_cuisine = tags.get("cuisine", "")
        cuisine = raw_cuisine.replace(";", ", ").replace("_", " ")
        cuisine_parts = {part.strip().lower().replace(" ", "_") for part in raw_cuisine.split(";") if part.strip()}
        if wanted and not wanted.intersection(cuisine_parts):
            continue
        if vegetarian and tags.get("diet:vegetarian") not in ("yes", "only", "limited"):
            continue
        if halal and tags.get("diet:halal") not in ("yes", "only", "limited"):
            continue
        opening_hours = tags.get("opening_hours", "")
        if open_now and not _is_open(opening_hours, weekday, minute_of_day):
            continue
        point = element if "lat" in element else element.get("center", {})
        if "lat" not in point or "lon" not in point:
            continue
        rlat, rlon = float(point["lat"]), float(point["lon"])
        key = f"osm-{element.get('type')}-{element.get('id')}"
        if key in seen:
            continue
        seen.add(key)
        found.append({"osm_id": key, "name": name, "cuisine": cuisine or "Local food", "category": tags.get("amenity", "restaurant").replace("_", " ").title(), "lat": rlat, "lon": rlon, "distance_m": round(_distance(lat, lon, rlat, rlon)), "address": ", ".join(filter(None, [tags.get("addr:street"), tags.get("addr:housenumber"), tags.get("addr:city")])), "opening_hours": opening_hours, "is_vegetarian": tags.get("diet:vegetarian", ""), "is_halal": tags.get("diet:halal", ""), "osm_url": f"https://www.openstreetmap.org/{element.get('type')}/{element.get('id')}"})
    return sorted(found, key=lambda item: (item["distance_m"], item["name"].lower()))


def _distance(lat1, lon1, lat2, lon2):
    radius = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def _is_open(hours, weekday, minute):
    """Best-effort evaluator for common OSM weekday and HH:MM ranges."""
    if weekday not in range(7) or minute not in range(1440) or not hours:
        return False
    if hours.strip() == "24/7":
        return True
    day_names = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
    today = day_names[weekday]
    for rule in hours.split(";"):
        rule = rule.strip()
        if not rule or "off" in rule.lower() or "closed" in rule.lower():
            continue
        day_part, time_part = "", rule
        if " " in rule:
            day_part, time_part = rule.split(None, 1)
        days = set(day_names)
        if day_part:
            days = set()
            for span in day_part.split(","):
                span = span.strip()
                if "-" in span:
                    first, last = span.split("-", 1)
                    if first not in day_names or last not in day_names:
                        continue
                    i, end = day_names.index(first), day_names.index(last)
                    while True:
                        days.add(day_names[i])
                        if i == end: break
                        i = (i + 1) % 7
                elif span in day_names:
                    days.add(span)
        if today not in days:
            continue
        for interval in time_part.split(","):
            if "-" not in interval:
                continue
            start, end = interval.strip().split("-", 1)
            try:
                a = int(start[:2])*60+int(start[3:5]); b = int(end[:2])*60+int(end[3:5])
            except (ValueError, IndexError):
                continue
            if a <= minute < b or (b < a and minute >= a):
                return True
    return False

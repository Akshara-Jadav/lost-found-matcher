import random
from datetime import date, timedelta
from pathlib import Path

from app.schemas import KNOWN_LOCATIONS
from app.storage import ReportStore

random.seed(7)                       # same data every run
OUTPUT = Path("data/sample_reports.json")
OUTPUT.unlink(missing_ok=True)       # start fresh each time

ITEMS = [
    ("earphones", "boat", "black", "earphones with case"),
    ("phone", "samsung", "blue", "phone with cracked screen"),
    ("bottle", "milton", "green", "steel water bottle"),
    ("wallet", "", "brown", "leather wallet"),
    ("keys", "", "silver", "bunch of keys with red keychain"),
    ("calculator", "casio", "grey", "scientific calculator"),
    ("bag", "wildcraft", "black", "backpack with laptop sleeve"),
    ("id_card", "", "white", "college id card"),
    ("books", "", "blue", "data structures textbook"),
]
places = sorted(KNOWN_LOCATIONS)
today = date.today()
store = ReportStore(OUTPUT)

for i in range(20):
    category, brand, color, desc = random.choice(ITEMS)
    place = random.choice(places)
    lost_date = today - timedelta(days=random.randint(0, 45))
    store.add("lost", category=category,
              description=f"{color} {brand} {desc}".replace("  ", " "),
              location=place, event_date=lost_date,
              contact=f"90000000{i:02d}", color=color, brand=brand)

    if random.random() < 0.6:        # about 60% get a found report too
        found_date = min(lost_date + timedelta(days=random.randint(0, 4)), today)
        store.add("found", category=category,
                  description=f"{desc} {color}",
                  location=random.choice([place, place, random.choice(places)]),
                  event_date=found_date, contact=f"80000000{i:02d}",
                  color=color, brand=brand,
                  verification_question="What mark or sticker is on it?",
                  verification_answer="blue sticker")

print(f"Created {len(store.list())} reports in {OUTPUT}")
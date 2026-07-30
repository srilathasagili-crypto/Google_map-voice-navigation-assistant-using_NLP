"""
Generates an expanded, realistic intent training dataset by combining
varied sentence templates with slot values (destinations, place types,
preferences). This produces genuine linguistic variety instead of just
duplicating a handful of hand-written examples.
"""

import csv
import random

random.seed(42)

# ---------------------------------------------------------------------
# NAVIGATE
# ---------------------------------------------------------------------
navigate_templates = [
    "navigate to {dest}",
    "take me to {dest}",
    "directions to {dest}",
    "i want to go to {dest}",
    "how do i get to {dest}",
    "guide me to {dest}",
    "route to {dest}",
    "show me the way to {dest}",
    "plot a route to {dest}",
    "head to {dest}",
    "get me to {dest}",
    "i need to reach {dest}",
    "can you take me to {dest}",
    "start navigation to {dest}",
    "let's go to {dest}",
    "i want directions to {dest}",
    "please navigate to {dest}",
    "set destination to {dest}",
]

destinations = [
    "central park", "the airport", "my office", "connaught place",
    "hyderabad railway station", "the nearest mall", "mg road",
    "the stadium", "my home", "secunderabad", "charminar", "the hotel",
    "the city center", "gachibowli", "banjara hills", "the metro station",
    "the bus stop", "my college", "downtown", "the beach", "the market",
    "jubilee hills", "hitech city", "the temple", "the movie theatre",
    "the railway station", "my friend's house", "the office park",
]

# ---------------------------------------------------------------------
# SEARCH NEARBY
# ---------------------------------------------------------------------
search_templates = [
    "find nearest {place}",
    "where is the closest {place}",
    "show me nearby {place}",
    "find a {place} near me",
    "i need a {place} nearby",
    "locate the nearest {place}",
    "show nearby {place}",
    "find {place} near my location",
    "nearest {place} please",
    "where can i find a {place} nearby",
    "is there a {place} close by",
    "search for {place} nearby",
    "any {place} around here",
    "i'm looking for a {place} nearby",
    "can you find a {place} close to me",
    "where's the nearest {place}",
]

place_phrases = [
    "hospital", "clinic", "atm", "cash machine", "petrol pump",
    "gas station", "fuel station", "pharmacy", "medical store",
    "restaurant", "food court", "coffee shop", "cafe", "bank",
    "parking", "parking lot", "grocery store", "supermarket",
    "ev charging station", "charging point",
]

# ---------------------------------------------------------------------
# TRAFFIC INFO (no slots — hand-varied)
# ---------------------------------------------------------------------
traffic_examples = [
    "how is the traffic right now",
    "is there heavy traffic on this route",
    "check traffic conditions",
    "what is the traffic like ahead",
    "any traffic jams on the way",
    "tell me about current traffic",
    "how busy is the road right now",
    "is the highway congested",
    "traffic update please",
    "how long will the traffic delay be",
    "what's the traffic situation",
    "is there a jam ahead",
    "how's the road looking right now",
    "any delays on my route",
    "is traffic clear right now",
    "give me a traffic report",
    "how congested is it right now",
    "will i hit traffic on this route",
    "is the road busy",
    "check the current traffic status",
]

# ---------------------------------------------------------------------
# ROUTE PREFERENCE
# ---------------------------------------------------------------------
route_pref_templates = [
    "{pref}",
    "please {pref}",
    "i want to {pref}",
    "can you {pref}",
    "make sure to {pref}",
    "i'd prefer to {pref}",
]

route_prefs = [
    "avoid highways for this route", "take the fastest route",
    "prefer the shortest path", "avoid tolls", "use the scenic route",
    "take a route without traffic", "prefer walking directions",
    "give me the quickest way", "avoid the highway",
    "switch to public transport route", "use driving directions only",
    "avoid toll roads", "take the route with least traffic",
    "prefer the route with no highways",
]

# ---------------------------------------------------------------------
# CANCEL
# ---------------------------------------------------------------------
cancel_examples = [
    "cancel the navigation", "stop navigation", "end the trip",
    "cancel this route", "stop giving directions", "cancel my trip",
    "stop the navigation now", "i want to cancel this route",
    "end navigation please", "stop directions", "quit navigation",
    "cancel current route", "turn off navigation", "exit navigation",
]

# ---------------------------------------------------------------------
# CURRENT LOCATION
# ---------------------------------------------------------------------
current_location_examples = [
    "what is my current location", "where am i right now",
    "tell me my current position", "show my location",
    "where am i currently", "what's my location right now",
    "can you tell me where i am", "locate me right now",
    "show me where i am on the map", "what location am i at",
    "where exactly am i", "pinpoint my current location",
    "i want to know my current location", "show current position",
    "tell me where i currently am", "display my location",
]


def build_dataset():
    rows = []

    # navigate: cross templates x destinations, sample to keep variety without full explosion
    combos = [(t, d) for t in navigate_templates for d in destinations]
    random.shuffle(combos)
    for t, d in combos[:90]:
        rows.append((t.format(dest=d), "navigate"))

    # search_nearby
    combos = [(t, p) for t in search_templates for p in place_phrases]
    random.shuffle(combos)
    for t, p in combos[:90]:
        rows.append((t.format(place=p), "search_nearby"))

    # traffic_info
    for ex in traffic_examples:
        rows.append((ex, "traffic_info"))
    # duplicate with slight variety multiplier isn't needed; keep as-is (20 examples)

    # route_preference
    combos = [(t, p) for t in route_pref_templates for p in route_prefs]
    random.shuffle(combos)
    for t, p in combos[:50]:
        rows.append((t.format(pref=p), "route_preference"))

    # cancel
    for ex in cancel_examples:
        rows.append((ex, "cancel"))

    # current_location
    for ex in current_location_examples:
        rows.append((ex, "current_location"))

    random.shuffle(rows)
    return rows


if __name__ == "__main__":
    rows = build_dataset()
    out_path = "../data/intents.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "intent"])
        writer.writerows(rows)

    from collections import Counter
    counts = Counter(intent for _, intent in rows)
    print(f"Total examples: {len(rows)}")
    for intent, count in counts.items():
        print(f"  {intent}: {count}")
    print(f"Saved to {out_path}")

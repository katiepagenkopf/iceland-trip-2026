#!/usr/bin/env python3
"""
Session 3: Content Cards for Iceland Trip
- Confirmation cards for reserved meals
- Backup restaurant cards (visually muted)
- Walk-in / Reserved badges
"""
from bs4 import BeautifulSoup
import re, os

REPO = os.path.expanduser("~/iceland-trip-2026")

# ─── Reservation data ───
RESERVATIONS = {
    "Grillmarkaðurinn": {
        "conf": "#8943063", "time": "8:00–10:00 PM", "guests": 3,
        "phone": "+354 571 7777", "url": "grillmarkadurinn.is",
        "addr": "Austurstræti 22, 101 Reykjavík", "type": "reserved"
    },
    "Gamli Baukur": {
        "conf": "#8943480", "time": "1:30–3:30 PM", "guests": 3,
        "phone": "+354 464 2350", "url": "glibbakur.is",
        "addr": "Húsavík harbour", "type": "reserved"
    },
    "Sjávarpakkhúsið": {
        "conf": "#8943622", "time": "6:00–8:00 PM", "guests": 3,
        "phone": "+354 438 1800", "url": "sjavarpakkhusid.is",
        "addr": "Stykkishólmur harbour", "type": "reserved"
    },
    "Messinn": {
        "conf": "#8943892", "time": "7:30–9:30 PM", "guests": 3,
        "phone": "+354 546 0095", "url": "messinn.com",
        "addr": "Lækjargata 6b, Reykjavík", "type": "reserved"
    },
}

# Walk-in meals (no Dineout reservation)
WALKINS = {
    "Friðheimar": {"note": "Walk-in · Geothermal tomatoes"},
    "Minilik": {"note": "Phone reservation · Ethiopian"},
    "Kjarr": {"note": "Walk-in, first come first served · 4.9★"},
    "Pakkhús": {"note": "Walk-in · Famous for lobster"},
    "Moroccan at Hotel Siglunes": {"note": "Reserved via hotel website"},
    "Eldey Restaurant": {"note": "On-site at Hótel Laxá"},
}

# Backup restaurants
BACKUPS = {
    "Friðheimar Winebar & Bistro": {
        "backup_name": "Farmers Bistro",
        "backup_conf": "#8943165",
        "backup_time": "2:30–4:00 PM",
        "backup_phone": "+354 519 0808",
        "backup_url": "farmersbistro.is",
        "backup_addr": "Flúðir",
        "backup_note": "If Friðheimar is packed",
    },
    "Kjarr": {
        "backup_name": "Klaustur Restaurant",
        "backup_conf": "#8943297",
        "backup_time": "7:30–9:00 PM",
        "backup_phone": "+354 487 1416",
        "backup_url": "klausturrestaurant.is",
        "backup_addr": "Kirkjubæjarklaustur",
        "backup_note": "If Kjarr has no tables",
    },
}

# ─── New CSS to inject ───
MEAL_CARD_CSS = """
  /* ── Session 3: Meal Detail Cards ── */
  .meal-detail-card {
    margin: 8px 0 4px 0;
    padding: 10px 12px;
    background: #F8F9FA;
    border-radius: 10px;
    border: 1px solid #E5E5EA;
  }
  .meal-detail-card .detail-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 3px 0;
    font-size: 13px;
    color: #636366;
  }
  .meal-detail-card .detail-row .detail-label {
    font-weight: 600;
    color: #8E8E93;
    min-width: 36px;
  }
  .meal-detail-card .detail-row .detail-value {
    color: #1C1C1E;
  }
  .meal-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    margin-bottom: 6px;
  }
  .badge-reserved {
    background: #E3F2FD;
    color: #1565C0;
  }
  .badge-walkin {
    background: #E8F5E9;
    color: #2E7D32;
  }
  .badge-backup {
    background: #FFF3E0;
    color: #E65100;
  }
  .backup-restaurant-card {
    margin: 6px 0 4px 0;
    padding: 10px 12px;
    background: #FFFBF0;
    border-radius: 10px;
    border: 1px dashed #FFD54F;
    opacity: 0.85;
  }
  .backup-restaurant-card .backup-header {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 4px;
  }
  .backup-restaurant-card .backup-label {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #E65100;
  }
  .backup-restaurant-card .backup-name {
    font-size: 15px;
    font-weight: 600;
    color: #1C1C1E;
  }
  .backup-restaurant-card .backup-subtitle {
    font-size: 13px;
    color: #636366;
    margin-top: 2px;
  }
  .backup-restaurant-card .detail-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 2px 0;
    font-size: 13px;
    color: #636366;
  }
  .backup-restaurant-card .detail-row .detail-label {
    font-weight: 600;
    color: #8E8E93;
    min-width: 36px;
  }
"""

def inject_css(soup):
    """Add meal card CSS before closing </style> tag."""
    style_tag = soup.find("style")
    if style_tag:
        style_tag.string += MEAL_CARD_CSS

def find_meal_items(soup):
    """Find all timeline items with dot-food."""
    items = []
    for dot in soup.find_all("div", class_="dot-food"):
        timeline_item = dot.find_parent("div", class_="timeline-item")
        if timeline_item:
            items.append(timeline_item)
    return items

def get_meal_name(item):
    """Extract the restaurant name from a timeline item."""
    title = item.find("div", class_="event-title")
    if title:
        text = title.get_text()
        # Strip prefixes like "Dinner: ", "Lunch: ", "Late lunch: "
        for prefix in ["Dinner: ", "Lunch: ", "Late lunch: ", "Breakfast: ", "Farewell dinner at "]:
            if text.startswith(prefix):
                return text[len(prefix):]
        return text
    return ""

def add_badge(item, badge_type):
    """Add a walk-in or reserved badge below the subtitle."""
    details = item.find("div", class_="event-details")
    if not details:
        return
    subtitle = details.find("div", class_="event-subtitle")
    if not subtitle:
        return
    
    # Don't add duplicate
    if details.find("div", class_="meal-badge"):
        return
    
    badge = soup.new_tag("div", **{"class": f"meal-badge badge-{badge_type}"})
    if badge_type == "reserved":
        badge.string = "🔑 Reserved"
    elif badge_type == "walkin":
        badge.string = "🚶 Walk-in"
    
    subtitle.insert_after(badge)

def add_confirmation_card(item, conf_data):
    """Add a meal detail card with confirmation info."""
    details = item.find("div", class_="event-details")
    if not details:
        return
    
    # Don't add duplicate
    if details.find("div", class_="meal-detail-card"):
        return
    
    # Remove old inline confirmation if present
    old_conf = details.find("div", style=re.compile("font-size:12px"))
    if old_conf:
        old_conf.decompose()
    
    card = soup.new_tag("div", **{"class": "meal-detail-card"})
    
    rows = [
        ("🔑", "Confirmation", conf_data["conf"]),
        ("🕐", "Time", conf_data["time"]),
        ("👥", "Guests", str(conf_data["guests"])),
        ("📞", "Phone", conf_data["phone"]),
        ("📍", "Address", conf_data["addr"]),
    ]
    
    for icon, label, value in rows:
        row = soup.new_tag("div", **{"class": "detail-row"})
        icon_span = soup.new_tag("span")
        icon_span.string = icon
        label_span = soup.new_tag("span", **{"class": "detail-label"})
        label_span.string = label
        value_span = soup.new_tag("span", **{"class": "detail-value"})
        value_span.string = value
        row.append(icon_span)
        row.append(label_span)
        row.append(value_span)
        card.append(row)
    
    # Insert card after badge (if present) or after subtitle
    badge = details.find("div", class_="meal-badge")
    subtitle = details.find("div", class_="event-subtitle")
    if badge:
        badge.insert_after(card)
    elif subtitle:
        subtitle.insert_after(card)

def add_backup_card(item, backup_data):
    """Add a backup restaurant card after the primary meal's timeline item."""
    card = soup.new_tag("div", **{"class": "backup-restaurant-card"})
    
    # Header
    header = soup.new_tag("div", **{"class": "backup-header"})
    badge = soup.new_tag("span", **{"class": "meal-badge badge-backup"})
    badge.string = "🔄 Backup"
    header.append(badge)
    card.append(header)
    
    # Name
    name_div = soup.new_tag("div", **{"class": "backup-name"})
    name_div.string = backup_data["backup_name"]
    card.append(name_div)
    
    # Subtitle
    subtitle = soup.new_tag("div", **{"class": "backup-subtitle"})
    subtitle.string = backup_data["backup_note"]
    card.append(subtitle)
    
    # Detail rows
    rows = [
        ("🔑", "Confirmation", backup_data["backup_conf"]),
        ("🕐", "Time", backup_data["backup_time"]),
        ("📞", "Phone", backup_data["backup_phone"]),
        ("📍", "Location", backup_data["backup_addr"]),
    ]
    
    for icon, label, value in rows:
        row = soup.new_tag("div", **{"class": "detail-row"})
        icon_span = soup.new_tag("span")
        icon_span.string = icon
        label_span = soup.new_tag("span", **{"class": "detail-label"})
        label_span.string = label
        value_span = soup.new_tag("span", **{"class": "detail-value"})
        value_span.string = value
        row.append(icon_span)
        row.append(label_span)
        row.append(value_span)
        card.append(row)
    
    # Insert after the timeline item
    item.insert_after(card)

def process_day(day_num):
    """Process a single day HTML file."""
    filepath = os.path.join(REPO, f"iceland-day{day_num}.html")
    if not os.path.exists(filepath):
        print(f"  ⚠️  {filepath} not found")
        return
    
    global soup
    with open(filepath, "r") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    
    # Inject CSS
    inject_css(soup)
    
    # Find all meal items
    meal_items = find_meal_items(soup)
    
    for item in meal_items:
        name = get_meal_name(item)
        
        # Check if this is a reserved meal
        matched = False
        for res_name, res_data in RESERVATIONS.items():
            if res_name.lower() in name.lower():
                add_badge(item, "reserved")
                add_confirmation_card(item, res_data)
                print(f"  ✅ Day {day_num}: Added reserved card for {res_name} ({res_data['conf']})")
                matched = True
                break
        
        if not matched:
            # Check walk-ins
            for walk_name, walk_data in WALKINS.items():
                if walk_name.lower() in name.lower():
                    add_badge(item, "walkin")
                    print(f"  🚶 Day {day_num}: Added walk-in badge for {walk_name}")
                    matched = True
                    break
        
        if not matched:
            # Generic fallback — check if it looks like a meal
            if any(w in name.lower() for w in ["breakfast", "hotel siglunes", "eldey"]):
                add_badge(item, "walkin")
                print(f"  🚶 Day {day_num}: Added walk-in badge for {name}")
        
        # Check if this meal has a backup
        for primary_name, backup_data in BACKUPS.items():
            if primary_name.lower() in name.lower():
                add_backup_card(item, backup_data)
                print(f"  🔄 Day {day_num}: Added backup card for {backup_data['backup_name']}")
    
    # Write back
    with open(filepath, "w") as f:
        f.write(str(soup))
    
    print(f"  📄 Day {day_num} saved")

# ─── Main ───
if __name__ == "__main__":
    print("🍽️ Session 3: Building meal content cards...\n")
    for day in range(1, 11):
        print(f"Day {day}:")
        process_day(day)
        print()
    print("✅ All meal cards built!")

import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import random
import re
import matplotlib.pyplot as plt

# Scrape Attractions

def scrape_holidify_attractions(dest):
    try:
        url = f"https://www.holidify.com/places/{dest.lower().replace(' ', '-')}/sightseeing-and-things-to-do.html"
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        attractions = [tag.get_text(strip=True) for tag in soup.select("h3.card-heading, h2.card-heading")]

        clean = []
        for a in attractions:
            a = re.sub(r"^\d+\.\s*", "", a).strip()
            if len(a) > 2:
                clean.append(a)
        return clean
    except Exception:
        return []


# 🏨 Scrape Hotels (Realistic + Budget Filtering)

def scrape_holidify_hotels(dest, budget, days):
    try:
        url = f"https://www.holidify.com/places/{dest.lower().replace(' ', '-')}/hotels-where-to-stay.html"
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select("div.card, div.hotelCard, div.card-content")

        hotel_budget_per_day = budget * 0.50  # ✅ 5%% per day of total budget
        valid_hotels = []

        for card in cards:
            # Hotel Name
            name_tag = card.select_one("h3.card-heading, h2.card-heading, a.card-heading")
            if not name_tag:
                continue
            name = name_tag.get_text(strip=True)

            # Hotel Price — Extract real value
            price_tag = card.select_one("div.price, span[data-testid='price'], span.price, div.hotelPrice")
            price_text = price_tag.get_text(strip=True) if price_tag else card.get_text(" ", strip=True)
            price_match = re.search(r"₹\s?([\d,]+)", price_text)

            if not price_match:
                continue  # skip hotels without visible price

            price = int(price_match.group(1).replace(",", ""))

            # Hotel Rating (if available)
            rating_match = re.search(r"(\d\.\d)", card.get_text())
            rating = float(rating_match.group(1)) if rating_match else round(random.uniform(3.5, 4.8), 1)

            # ✅ Only include realistic hotels under daily budget limit
            if price <= hotel_budget_per_day:
                valid_hotels.append({"name": name, "price": price, "rating": rating})

        # Fallback hotels if none found
        if not valid_hotels:
            valid_hotels = [
                {"name": "Budget Stay", "price": 1200, "rating": 3.9},
                {"name": "Hotel Comfort Inn", "price": 1400, "rating": 4.2},
                {"name": "City Lodge", "price": 1000, "rating": 4.0},
            ]

        return valid_hotels[:10]
    except Exception as e:
        print("⚠️ Hotel scraping error:", e)
        return []

# 🎯 Filter Attractions

def filter_attractions(attractions, preferences):
    if not preferences or "all" in preferences:
        return attractions

    category_keywords = {
        "historical": ["fort", "palace", "temple", "monument", "heritage", "gate", "tomb"],
        "fun": ["beach", "park", "zoo", "amusement", "island", "water", "lake"],
        "museum": ["museum", "gallery", "memorial", "exhibition", "centre", "art"],
        "nature": ["hill", "mountain", "valley", "garden", "wildlife", "forest", "sanctuary"]
    }

    selected_keywords = []
    for pref in preferences:
        selected_keywords.extend(category_keywords.get(pref, []))
    selected_keywords = list(set(selected_keywords))

    filtered = [a for a in attractions if any(kw in a.lower() for kw in selected_keywords)]
    return filtered

# 🧮 Generate Travel Plan

def generate_plan(destination, budget, days, preferences, food_type):
    attractions = scrape_holidify_attractions(destination)
    hotels = scrape_holidify_hotels(destination, budget, days)
    attractions = filter_attractions(attractions, preferences)

    if not attractions:
        attractions = ["Local Market Visit", "City Park", "Sunset Point", "Cultural Walk"]

    hotel = random.choice(hotels)
    hotel_cost = hotel["price"]
    food_cost = random.randint(400, 700) if food_type == "vegetarian" else random.randint(600, 900)
    transport = random.randint(600, 2000)
    shopping_tours = round(budget * 0.30, 2)
    total_core = (hotel_cost * days) + (food_cost * days) + transport
    total_trip_cost = total_core + shopping_tours

    random.shuffle(attractions)
    per_day = max(1, len(attractions) // days)
    itinerary = {f"Day {i+1}": attractions[i*per_day:(i+1)*per_day] for i in range(days)}

    return {
        "Destination": destination,
        "Hotel": hotel,
        "Hotel Cost": hotel_cost,
        "Food Cost": food_cost,
        "Transport": transport,
        "Shopping": shopping_tours,
        "Total Cost": total_trip_cost,
        "Itinerary": itinerary
    }

# -------------------------------
# 🌴 STREAMLIT APP
# -------------------------------
st.set_page_config(page_title="TripBuddy", page_icon="🌍", layout="centered")
st.title("🌴 TripBuddy - Smart Travel Planner")

with st.form("planner"):
    destination = st.text_input("Enter destination (e.g., Goa, Shimla, Jaipur)").title()
    budget = st.number_input("Enter your total budget (₹)", min_value=1000, step=500)
    days = st.number_input("Number of days", min_value=1, step=1)
    preferences = st.multiselect("Select attraction types", ["all", "historical", "fun", "museum", "nature"])
    food_type = st.radio("Food Preference", ["vegetarian", "non-vegetarian"])
    submit = st.form_submit_button("✨ Generate My Plan")

if submit:
    if not destination:
        st.warning("Please enter a valid destination.")
    else:
        with st.spinner("Building your perfect trip..."):
            plan = generate_plan(destination, budget, days, preferences, food_type)

        st.success("✅ Plan Generated Successfully!")

        st.subheader(f"📍 Destination: {plan['Destination']}")
        st.write(f"🏨 Hotel: {plan['Hotel']['name']}")
        st.write(f"⭐ Rating: {plan['Hotel']['rating']}")
        st.write(f"💵 Cost per day: ₹{plan['Hotel Cost']:,}")
        st.write(f"🍱 Food ({food_type}): ₹{plan['Food Cost']}/day")
        st.write(f"🚗 Transport: ₹{plan['Transport']}")
        st.write(f"🛍️ Shopping & Tours: ₹{plan['Shopping']}")
        st.markdown("---")

        st.subheader("🗓️ Itinerary")
        for day, acts in plan["Itinerary"].items():
            st.markdown(f"**{day}:**")
            for a in acts:
                st.write(f"• {a}")

        st.markdown("---")
        st.subheader("📊 Expense Breakdown")

        df = pd.DataFrame({
            "Category": ["Hotel", "Food", "Transport", "Shopping & Tours"],
            "Cost (₹)": [
                plan["Hotel Cost"] * days,
                plan["Food Cost"] * days,
                plan["Transport"],
                plan["Shopping"]
            ]
        })
        st.dataframe(df)

        fig, ax = plt.subplots()
        ax.pie(df["Cost (₹)"], labels=df["Category"], autopct="%1.1f%%", startangle=140)
        plt.title(f"Expense Breakdown for {destination}")
        st.pyplot(fig)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Report (CSV)", csv, f"{destination}_trip_report.csv", "text/csv")

        st.markdown("✨ _Powered by Holidify & TripBuddy_")

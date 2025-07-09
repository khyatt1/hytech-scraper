import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import base64

# --- 🔐 Simple Password Login ---
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Incorrect password")
        return False
    else:
        return True

if not check_password():
    st.stop()

# --- 🧠 Scraper Logic ---
st.set_page_config(page_title="HyTech Web Scraper", layout="wide")
st.title("📊 HyTech Web Scraper & Comparison Tool")

def get_page_content(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return BeautifulSoup(response.text, 'html.parser')
        return None
    except:
        return None

def extract_text_by_keywords(soup, keywords):
    if not soup:
        return "Error"
    text = soup.get_text(separator=' ').lower()
    for keyword in keywords:
        if keyword.lower() in text:
            return "Found"
    return "Not Found"

def scrape_rating(url):
    soup = get_page_content(url)
    if not soup:
        return "Error"
    for tag in soup.find_all(['span', 'div']):
        text = tag.get_text(strip=True)
        if "rating" in text.lower() and any(char.isdigit() for char in text):
            return text
    return "Not found"

def count_images(url):
    soup = get_page_content(url)
    if not soup:
        return "Error"
    return len(soup.find_all('img'))

def find_hero_photo(url):
    soup = get_page_content(url)
    if not soup:
        return "Error"
    imgs = soup.find_all('img')
    if not imgs:
        return "No images found"
    for img in imgs:
        width = img.get('width')
        if width and str(width).isdigit() and int(width) >= 600 and img.get('src'):
            return img['src']
    return imgs[0]['src'] if imgs[0].get('src') else "Not found"

def process_column(column, url):
    if not isinstance(url, str) or not url.startswith("http"):
        return "Invalid URL"
    keywords_map = {
        "Check-In": ["check-in", "arrival"],
        "Check-Out": ["check-out", "departure"],
        "Pool": ["pool", "swimming", "jacuzzi", "spa"],
        "Restaurant": ["restaurant", "dining", "meals", "breakfast"],
        "Renovation": ["renovation", "updated", "remodel", "construction"],
        "Amenity": ["fees", "charges", "amenity", "resort fee", "tax"],
        "Guest Messaging": ["message", "guest", "contact", "chat", "communication"],
        "Room Type": ["room", "suite", "bed", "accommodation"],
        "Content Score": ["score", "quality", "details"],
        "Other Details": ["details", "info", "description"]
    }

    if column == "Current Rating":
        return scrape_rating(url)
    elif column == "No. of Images":
        return count_images(url)
    elif column == "Hero Photo?":
        return find_hero_photo(url)
    elif column == "Page Placement":
        soup = get_page_content(url)
        if not soup:
            return "Error"
        return soup.find('h1').text.strip() if soup.find('h1') else "Not Found"
    else:
        for key in keywords_map:
            if key.lower() in column.lower():
                return extract_text_by_keywords(get_page_content(url), keywords_map[key])
        return extract_text_by_keywords(get_page_content(url), [column])

# --- Upload and Process ---
uploaded_file = st.file_uploader("📤 Upload your CSV file", type=["csv"])
if uploaded_file:
    df_input = pd.read_csv(uploaded_file, encoding="ISO-8859-1")
    df_input = df_input.loc[:, ~df_input.columns.str.contains("^Unnamed")]
    st.subheader("📥 Uploaded Data")
    st.dataframe(df_input)

    st.subheader("🔍 Scraping Results")
    results = []

    for index, row in df_input.iterrows():
        result_row = {}
        for col in df_input.columns:
            result_row[col] = process_column(col, row[col])
        result_row["Website"] = urlparse(row[0]).netloc if isinstance(row[0], str) else f"Row {index+1}"
        results.append(result_row)

    df_results = pd.DataFrame(results)
    df_results = df_results[["Website"] + [col for col in df_results.columns if col != "Website"]]
    st.dataframe(df_results)

    csv = df_results.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="comparison_results.csv">📥 Download Results as CSV</a>'
    st.markdown(href, unsafe_allow_html=True)


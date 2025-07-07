import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import base64

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
    elif "Check-In" in column:
        return extract_text_by_keywords(get_page_content(url), ["check-in", "arrival"])
    elif "Check-Out" in column:
        return extract_text_by_keywords(get_page_content(url), ["check-out", "departure"])
    elif "Pool" in column:
        return extract_text_by_keywords(get_page_content(url), ["pool", "jacuzzi", "spa"])
    elif "Restaurant" in column:
        return extract_text_by_keywords(get_page_content(url), ["restaurant", "dining", "breakfast"])
    elif "Renovation" in column:
        return extract_text_by_keywords(get_page_content(url), ["renovation", "updated", "remodel"])
    elif "Amenity Fee" in column or "Taxes and Fees" in column:
        return extract_text_by_keywords(get_page_content(url), ["fees", "charges", "amenity", "tax"])
    elif "Guest Messaging" in column:
        return extract_text_by_keywords(get_page_content(url), ["message", "guest", "contact", "communication"])
    elif "Room Type" in column:
        return extract_text_by_keywords(get_page_content(url), ["room", "suite", "bed", "type"])
    elif "Content Score" in column:
        return extract_text_by_keywords(get_page_content(url), ["score", "quality", "content"])
    elif "Other Details" in column:
        return extract_text_by_keywords(get_page_content(url), ["details", "additional", "info"])
    else:
        return extract_text_by_keywords(get_page_content(url), [column])

uploaded_file = st.file_uploader("📤 Upload your CSV file", type=["csv"])
if uploaded_file:
    df_input = pd.read_csv(uploaded_file, encoding="ISO-8859-1")
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

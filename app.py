import streamlit as st
from bs4 import BeautifulSoup
import pandas as pd
import streamlit.components.v1 as components
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin, urlparse
import io
import logging
import re

if 'url' not in st.session_state:
    st.session_state['url'] = ''
if 'scraped_data' not in st.session_state:
    st.session_state['scraped_data'] = None

# Initialize logger
logging.basicConfig(level=logging.ERROR)

# Function to scrape data using Selenium for dynamic content handling
@st.cache_data # Cache the function to improve performance
def scrape_dynamic_data(url, element_type):
    try:
        chrome_service = ChromeService(ChromeDriverManager().install())
        options = ChromeOptions()
        options.headless = True

        with webdriver.Chrome(service=chrome_service, options=options) as driver:
            driver.get(url)
            content = driver.page_source
            soup = BeautifulSoup(content, 'html.parser')

            if element_type == "tables":
                tables = soup.find_all('table')
                return [pd.read_html(str(table))[0] for table in tables]
            elif element_type == "images":
                images = soup.find_all('img')
                base_url = '{uri.scheme}://{uri.netloc}'.format(uri=urlparse(url))
                return [urljoin(base_url, img['src']) for img in images if img.get('src')]
            elif element_type == "links":
                return [a['href'] for a in soup.find_all('a', href=True)]
            elif element_type == "text":
                return soup.get_text()
            else:
                return None
    except Exception as e:
        st.error(f"An error occurred: {e}")
        logging.error(f"An error occurred while scraping {url}: {e}")
        return None

# Function to display data with pagination
def show_data_with_pagination(data, rows_per_page):
    page_num = st.number_input('Select Page', min_value=1, max_value=max(1, len(data) // rows_per_page + 1), step=1) - 1
    start = page_num * rows_per_page
    end = start + rows_per_page
    return data[start:end]

# Streamlit App
st.title("Advanced Web Scraping App")

url = st.text_input("Enter the URL of the website you want to scrape:", value=st.session_state['url'])
st.session_state['url'] = url
element_type = st.selectbox("Select the type of data to scrape:", ["tables", "images", "links", "text"])

if st.button("Scrape Data"):
    if url and element_type:
        with st.spinner('Scraping data...'):
            scraped_data = scrape_dynamic_data(url, element_type)

        if scraped_data:
            st.session_state['scraped_data'] = scraped_data
            st.success("Data scraped successfully!")

            if element_type == "tables":
                for i, df in enumerate(scraped_data):
                    st.subheader(f"Table {i + 1}")
                    st.write(df)
        
                    # Format selection
                    format_selection = st.selectbox(f"Select Format for Table {i + 1}", 
                                        ["CSV", "Excel", "JSON"], key=f"format_{i}")

                # Convert to selected format and provide download
                    if format_selection == "CSV":
                        csv_data = df.to_csv(index=False)
                        st.download_button(f"Download Table {i + 1} as CSV", csv_data, 
                               file_name=f"table_{i+1}.csv", mime="text/csv")
                    elif format_selection == "Excel":
                        excel_data = io.BytesIO()
                        with pd.ExcelWriter(excel_data, engine="xlsxwriter") as writer:
                            df.to_excel(writer, index=False)
                        st.download_button(f"Download Table {i + 1} as Excel", excel_data.getvalue(), 
                               file_name=f"table_{i+1}.xlsx", mime="application/vnd.ms-excel")
                    elif format_selection == "JSON":
                        json_data = df.to_json()
                        st.download_button(f"Download Table {i + 1} as JSON", json_data, 
                               file_name=f"table_{i+1}.json", mime="application/json")
            
            elif element_type == "images":
                # Display images
                for img in scraped_data:
                    st.image(img)
            
            elif element_type == "links":
                # Pagination for displaying links
                paginated_links = show_data_with_pagination(scraped_data, 10)
                for link in paginated_links:
                    st.write(link)

            elif element_type == "text":
                # Display text
                regex = st.text_input("Enter a regular expression to search in the text:")
                if regex:
                    matches = re.findall(regex, scraped_data)
                    st.subheader("Regex Search Results")
                    st.write(matches)
                else:
                    st.text(scraped_data)

        else:
            st.error("Failed to scrape data from the provided URL.")
    else:
        st.warning("Please enter a valid URL and select a data type.")

# Ethical Scraping Guidelines
st.sidebar.header("Ethical Scraping Guidelines")
st.sidebar.write("1. Always respect the website's terms of service.")
st.sidebar.write("2. Do not overload the website's server with requests.")
st.sidebar.write("3. Comply with the website's robots.txt file.")

st.info("This app is for educational purposes only. Be sure to respect the website's terms of service and policies when scraping data.")

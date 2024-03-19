import streamlit as st
import pandas as pd

import requests
import selenium
from selenium import webdriver
import time

import os
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException, ElementNotInteractableException, InvalidElementStateException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import base64
import io
from sqlalchemy import create_engine
from PIL import Image
import requests
from io import BytesIO
import mysql.connector



def main():
    global data
    title_container1 = st.container()
    col1, col2 = st.columns([6, 12])

    from PIL import Image
    image = Image.open('static/BMI.png')

    with title_container1:
        with col1:
            st.image(image, width=705)
        with col2:
            st.markdown('<h1 style="color: red;"></h1>', unsafe_allow_html=True)

    st.sidebar.image("static/download.jpg", use_column_width=True)
    activities = ["Restaurant price validation"]
    choice = st.sidebar.selectbox("Select Activity", activities)

    
    
    if choice == 'Restaurant price validation':
        
        # Database credentials and details
        username = 'khurram'
        password = 'khurram@fooza@2022'
        host = 'fooza.cjitcsv9n7oy.ap-south-1.rds.amazonaws.com'
        database = 'fooza'
        
        # Establish the connection
        connection = mysql.connector.connect(
            host=host,
            user=username,
            password=password,
            database=database
        )
        
        st.markdown('**Click the button below to Load the data**')
        # Button to fetch data
        # Button to fetch data
        if st.button('Load the Data'):
            try:
                if 'df2' not in st.session_state or st.session_state.df2 is None:
                    # SQL Query for df2
                    query1 = """
                    select * from fooza.abserve_restaurants
                    where root_id=0
                    and restaurant_type = 'LIVE'
                    and status =1 and admin_status = 'Approved'
                    """
                    st.session_state.df2 = pd.read_sql_query(query1, connection)
        
                if 'df1' not in st.session_state or st.session_state.df1 is None:
                    # SQL Query for df1
                    query2 = """
                    SELECT r.l_id as Location, r.Status as ResStatus,   
                    r.admin_status as ResAdminStatus, r.mode as ResMode, r.partner_id as "Partner ID", p.username as PartnerName,p.phone_number, m.username as RM,m.email as RM_email,
                     r.id, r.name as ResName, c.cat_name as Category,r.adrs_line_2,r.sub_loc_level_1,r.city,
                    i.id as "Item ID" , i.food_item, i.status as "Veg/Non", i.item_status as "Stock Status",i.item_status,
                     i.selling_price, i.image,r.restaurant_network
                     FROM  fooza.abserve_restaurants r 
                     LEFT  join fooza.tb_users p ON r.partner_id = p.id 
                      LEFT  join  fooza.tb_users m ON p.manager_id = m.id
                      LEFT join fooza.abserve_hotel_items i on i.restaurant_id = r.id
                      left join fooza.abserve_food_categories c on c.id = i.main_cat
                     WHere restaurant_type = 'LIVE' and r.root_id = 0
                     and r.status =1 and r.admin_status = 'Approved' 
                     and i.approveStatus = 'Approved' and i.del_status = 0
                     
                     
                     order by r.status, r.admin_status, r.id, i.main_cat, i.food_item
                    """
                    st.session_state.df1 = pd.read_sql_query(query2, connection)
        
                st.markdown('**Data has been loaded successfully**')
            except Exception as e:
                st.error(f"An error occurred while loading data: {e}")
            finally:
                connection.close()
        
        if 'df1' in st.session_state and 'df2' in st.session_state:
            df2 = st.session_state.df2
            df1 = st.session_state.df1
                 
                
            ds = pd.read_excel('static/url_list.xlsx') # for xlsx file
            df1=df1[['id','Item ID','ResMode','restaurant_network','ResName','food_item','selling_price','RM','RM_email','PartnerName','phone_number']]
            df2=df2[['id','restaurant_type','restaurant_pos','location','name']]
            
            mer_df = pd.merge(df1, df2, on='id', how='left')
            mer_df = pd.merge(mer_df, ds[['id','zomato', 'swigy']], on='id', how='left')
            print(mer_df)
            
            unique_rms = df1['RM'].dropna().unique()
            unique_rms.sort()  # Sort RM names alphabetically, optional
            
            selected_rm = st.selectbox("Select a Restaurant Manager", unique_rms)
            filtered_restaurants = mer_df[mer_df['RM'] == selected_rm]
            
            st.subheader('Select the restaurant ID')
            
            
            # Optional: Text input for searching
            
            search_query = st.text_input("Search for a Restaurant with restaurant ID or name")

            # Convert search query to lowercase string for comparison
            search_query_str = str(search_query).lower()
            
            # Filter options based on search query within the filtered restaurants
            filtered_options_set = set(
                (int(row['id']), row['name']) for index, row in filtered_restaurants.iterrows()
                if search_query_str in row['name'].lower() or search_query_str in str(row['id'])
            )
            
            # Convert the set back to a sorted list for the dropdown
            filtered_options = sorted(list(filtered_options_set), key=lambda x: x[1])  # Sort by restaurant name
            
            # Dropdown for filtered restaurant selection
            if filtered_options:
                selected_restaurant = st.selectbox(
                    "Select a Restaurant",
                    filtered_options,
                    format_func=lambda x: f"{x[1]} (ID: {x[0]})"
                )
                x = selected_restaurant[0]  # Extracting the ID of the selected restaurant
            else:
                st.write("No restaurants found for the selected RM and search criteria.")
                x = None
            # Button to confirm the selection
            #chromedriver_path = st.text_input('Enter the path to your Chromedriver on the desktop:', '')
            if st.button('Confirm Selection'):
                # The rest of the code that depends on x should be inside this block
                if x is not None:
                    merged_df=mer_df[mer_df['id'] == x]
                    merged_df['zomato'] = merged_df['zomato'].apply(lambda x: x + "/order" if pd.notnull(x) else x)
                    merged_df=merged_df.reset_index(drop=True)
                    if not merged_df.empty:
                        y=merged_df['name'][0]
                        
                        import os
                        desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')

                        # Assuming the Chromedriver is named 'chromedriver' or 'chromedriver.exe' and located on the desktop
                        chromedriver_name = 'chromedriver.exe' if os.name == 'nt' else 'chromedriver'
                        chromedriver_path = os.path.join(desktop_path, chromedriver_name)
                        
                        if os.path.exists(chromedriver_path):
                            # Initialize the Selenium Service with the path
                            s = Service(chromedriver_path)
                            driver = webdriver.Chrome(service=s)
                            # Your scraping logic here
                        else:
                            st.error(f'Chromedriver not found on the desktop. Expected path: {chromedriver_path}')
                                                
                        url=merged_df.zomato[0]
                        z_resname = []
                        z_loca = []
                        z_timing = []
                        if pd.notna(url) and url.strip() != "":
                            
                            page = (driver.get(url))
                            wait = WebDriverWait(driver,3)
                            xpath = f"//a[@href='{page}']"
                        
                        
                            try:
                                wait.until(EC.element_to_be_clickable((By.XPATH, xpath))).click()
                            except TimeoutException:
                                pass
                        
                        
                            scroll_amount = 100
                        
                            while True:
                                # Scroll down gradually
                                driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                        
                                # Wait briefly to mimic the scrolling speed
                                time.sleep(0.1)  # Adjust this sleep duration as needed
                        
                                # Check if you have reached the bottom of the page
                                if driver.execute_script("return (window.innerHeight + window.scrollY) >= document.body.scrollHeight"):
                                    break
                        
                            # Scroll back up to a specific position (e.g., 300 pixels from the top)
                            driver.execute_script("window.scrollTo(0, 300)")
                        
                            while True:
                                try:
                                    element = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[@class='sc-ya2zuu-0 SWRrQ']"))).click() 
                        
                                except TimeoutException:
                                    # Element not found, break the loop
                                    break
                            scroll_amount = 100
                        
                            while True:
                                # Scroll down gradually
                                driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                        
                                # Wait briefly to mimic the scrolling speed
                                time.sleep(0.1)  # Adjust this sleep duration as needed
                        
                                # Check if you have reached the bottom of the page
                                if driver.execute_script("return (window.innerHeight + window.scrollY) >= document.body.scrollHeight"):
                                    break
                        
                        
                            item_name = []
                            item_price = []
                            
                        
                            scroll_amount = -300  # Negative value for scrolling up
                            scroll_duration = 0.1  # Adjust this duration as needed
                        
                            # Scroll to the top gradually
                            while True:
                                driver.execute_script(f"window.scrollBy(0, {scroll_amount})")
                                time.sleep(scroll_duration)
                        
                                # Check if you have reached the top of the page
                                if driver.execute_script("return window.scrollY <= 0"):
                                    # If you've reached the top, stop scrolling
                                    break
                            # Flag to keep track of whether all data has been captured
                            all_data_captured = False
                        
                            while not all_data_captured:
                        
                        
                                # Scrape data for item_name
                                try:
                                    elements = driver.find_elements(by=By.XPATH,value="//div[@class='sc-1s0saks-13 kQHKsO']/h4")
                        
                                    for element in elements:
                                        item_name.append(element.text)
                        
                                except NoSuchElementException:
                                    item_name.append("NA")
                        
                                # Scrape data for item_price
                                try:
                                    elements = driver.find_elements(by=By.XPATH,value="//div[@class='sc-17hyc2s-3 jOoliK sc-1s0saks-8 gYkxGN']/span")
                        
                                    for element in elements:
                                        price_text = element.text.replace('₹', '').strip()
                                        item_price.append(price_text)
                        
                                except NoSuchElementException:
                                    item_price.append("NA")
                        
                                try:
                                    elements = driver.find_elements(by=By.XPATH,value="//div[@class='sc-jeCdPy brTljW']/h1")
                        
                                    for element in elements:
                                        z_resname.append(element.text)
                        
                                except NoSuchElementException:
                                    z_resname.append("NA")
                                    
                                try:
                                    elements = driver.find_elements(by=By.XPATH,value="//a[@class='sc-clNaTc vNCcy']")
                        
                                    for element in elements:
                                        z_loca.append(element.text)
                        
                                except NoSuchElementException:
                                    z_loca.append("NA")
                                    
                                try:
                                    elements = driver.find_elements(by=By.XPATH,value="//span[@class='sc-kasBVs dfwCXs']")
                        
                                    for element in elements:
                                        z_timing.append(element.text)
                        
                                except NoSuchElementException:
                                    z_timing.append("NA")
                        
                        
                                # Check if all data has been captured
                                if len(item_name) == len(item_price):
                                    all_data_captured = True
                                else:
                                    # If not all data has been captured, break out of the loop
                                    break
                        
                                # If not all data has been captured, go back or perform necessary actions to load more data on the page
                                # You can add code here to navigate to the next page or perform any necessary actions
                                
                                
                            
                        
                            # Ensure all lists are the same length by filling with "NA"
                            max_length = max(len(item_name), len(item_price))
                        
                            item_name += ['NA'] * (max_length - len(item_name))
                            item_price += ['NA'] * (max_length - len(item_price))
                        
                        
                            # Create a DataFrame
                            data = {
                        
                                'Item Name': item_name,
                                'Item Price': item_price
                        
                            }
                        
                            df = pd.DataFrame(data)
                        
                        else:
                            # If the URL is null or NaN, create an empty DataFrame with only column names
                            df = pd.DataFrame(columns=['Item Name', 'Item Price'])
                        z_deta = ', '.join(z_resname if isinstance(z_resname, list) else [z_resname])
                        z_deta += ', ' + ', '.join(z_loca if isinstance(z_loca, list) else [z_loca])
                        z_deta += ', ' + ', '.join(z_timing if isinstance(z_timing, list) else [z_timing])
                        url=merged_df.swigy[0]
                        s_resname =[]
                        s_loca=[]
                        if pd.notna(url) and url is not None:
                            driver.get(url)
                        
                            wait = WebDriverWait(driver,2)
                        
                            scroll_amount = 400
                        
                            while True:
                                # Scroll down gradually
                                driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                        
                                # Wait briefly to mimic the scrolling speed
                                time.sleep(0.1)  # Adjust this sleep duration as needed
                        
                                # Check if you have reached the bottom of the page
                                if driver.execute_script("return (window.innerHeight + window.scrollY) >= document.body.scrollHeight"):
                                    break
                        
                            # Scroll back up to a specific position (e.g., 300 pixels from the top)
                            driver.execute_script("window.scrollTo(0, 400)")
                        
                        
                        
                            item_name = []
                            item_price = []
                            
                        
                            all_data_captured = False
                        
                            while not all_data_captured:
                        
                                try:
                                    elements = driver.find_elements(by=By.XPATH,value="//div[@class='styles_itemName__hLfgz']/h3")
                        
                                    for element in elements:
                                        item_name.append(element.text)
                        
                                except NoSuchElementException:
                                    item_name.append("NA")
                        
                                try:
                                    elements = driver.find_elements(by=By.XPATH,value="//div[@class='styles_itemPortionContainer__1u_tj']/span")
                        
                                    for element in elements:
                                        item_price.append(element.text)
                        
                                except NoSuchElementException:
                                    item_price.append("NA")
                        
                        
                                try:
                                    elements = driver.find_elements(by=By.XPATH,value="//p[@class='RestaurantNameAddress_name__2IaTv']")
                        
                                    for element in elements:
                                        s_resname.append(element.text)
                        
                                except NoSuchElementException:
                                    s_resname.append("NA")
                                    
                                try:
                                    elements = driver.find_elements(by=By.XPATH,value="//p[@class='RestaurantNameAddress_area__2P9ib']")
                        
                                    for element in elements:
                                        s_loca.append(element.text)
                        
                                except NoSuchElementException:
                                    s_loca.append("NA")
                        
                                # Check if all data has been captured
                                if len(item_name) == len(item_price):
                                    all_data_captured = True
                                else:
                                    # If not all data has been captured, break out of the loop
                                    break
                        
                            driver.quit()
                        
                            # Ensure all lists are the same length by filling with "NA"
                            max_length = max( len(item_name), len(item_price))
                        
                            item_name += ['NA'] * (max_length - len(item_name))
                            item_price += ['NA'] * (max_length - len(item_price))
                        
                        
                            # Create a DataFrame
                            data = {
                        
                                'Item Name': item_name,
                                'Item Price': item_price
                        
                            }
                        
                            dfs = pd.DataFrame(data)
                            
                        else:
                            # If the URL is null or NaN, create an empty DataFrame with only column names
                            dfs = pd.DataFrame(columns=['Item Name', 'Item Price'])
                            driver.quit()
                        s_deta = ', '.join(s_resname if isinstance(s_resname, list) else [s_resname])
                        s_deta += ', ' + ', '.join(s_loca if isinstance(s_loca, list) else [s_loca])
                        columns_to_display = ['food_item', 'selling_price','Item ID']

                        filtered_df = df1[df1['id'] == x][columns_to_display]
                        filtered_df=filtered_df.reset_index(drop=True)
                        
                        
                        df_zomato=df[['Item Name','Item Price']]
                        from fuzzywuzzy import fuzz
                        import re
                        
                        # Function for text normalization: remove non-alphanumeric characters, keep spaces
                        def normalize_text(text):
                            return re.sub(r'[^a-zA-Z0-9 ]', '', text.lower())
                        
                        # Function to handle special abbreviations, plurals, and remove specific terms
                        def preprocess_item_name(text):
                            text = text.lower()
                            text = text.replace('b/l', 'boneless').replace('bl', 'boneless')
                            text = re.sub(r'chow(?!mein)', 'chowmein', text)
                            text = re.sub(r'\(full\)|\(half\)|&|with|off', '', text)
                        
                            # Treat 'fried' as optional for items containing 'rice'
                            if 'rice' in text:
                                text = re.sub(r' fried', '', text)
                        
                            # Remove extra spaces and handle plural forms
                            words = text.split()
                            processed_words = [word[:-1] if word.endswith('s') else word for word in words]
                            return ' '.join(processed_words).strip()
                        
                        # Function to check if the price is within 40% range
                        def price_within_range(db_price, other_price, threshold=0.4):
                            try:
                                other_price = float(other_price)
                            except ValueError:
                                return False
                            return abs(db_price - other_price) <= (db_price * threshold)
                        
                        # Fuzzy Matching function with token sort ratio and partial ratio
                        def fuzzy_match(db_item, other_items, threshold=85):
                            db_item_processed = preprocess_item_name(normalize_text(db_item))
                            best_match = None
                            highest_score = 0
                        
                            for item in other_items:
                                item_processed = preprocess_item_name(normalize_text(item))
                                token_score = fuzz.token_sort_ratio(db_item_processed, item_processed)
                                partial_score = fuzz.partial_ratio(db_item_processed, item_processed)
                                score = max(token_score, partial_score)
                        
                                if score > highest_score:
                                    highest_score = score
                                    best_match = item
                        
                            return (best_match, highest_score) if highest_score >= threshold else (None, None)
                        
                        
                        # Fuzzy Matching for Swiggy and Zomato datasets
                        matched_results = []
                        
                        for _, row in filtered_df.iterrows():
                            # Swiggy matching
                            swiggy_match, swiggy_score = fuzzy_match(row['food_item'], dfs['Item Name'].tolist())
                            swiggy_name, swiggy_price = "Not Matching", None
                            if swiggy_match:
                                swiggy_index = dfs[dfs['Item Name'] == swiggy_match].index[0]
                                if price_within_range(row['selling_price'], dfs.iloc[swiggy_index]['Item Price']):
                                    swiggy_name = dfs.iloc[swiggy_index]['Item Name']
                                    swiggy_price = dfs.iloc[swiggy_index]['Item Price']
                        
                            # Zomato matching
                            zomato_match, zomato_score = fuzzy_match(row['food_item'], df_zomato['Item Name'].tolist())
                            zomato_name, zomato_price = "Not Matching", None
                            if zomato_match:
                                zomato_index = df_zomato[df_zomato['Item Name'] == zomato_match].index[0]
                                if price_within_range(row['selling_price'], df_zomato.iloc[zomato_index]['Item Price']):
                                    zomato_name = df_zomato.iloc[zomato_index]['Item Name']
                                    zomato_price = df_zomato.iloc[zomato_index]['Item Price']
                                else:
                                    zomato_name = df_zomato.iloc[zomato_index]['Item Name']  # or keep it "Not Matching" if preferred
                                    zomato_price = df_zomato.iloc[zomato_index]['Item Price']
                            
                            
                        
                            # Construct the URL based on item_id
                            item_url = f"https://fooza.in/fooditems/update/{row['Item ID']}?page=1"
                        
                            matched_results.append((row['food_item'], row['selling_price'], swiggy_name, swiggy_price, zomato_name, zomato_price, item_url))
                        
                        # Create DataFrame with the additional URL column
                        matched_df = pd.DataFrame(matched_results, columns=['Fooza Food Name', 'Fooza Price', 'Swiggy Food Name', 'Swiggy Price', 'Zomato Food Name', 'Zomato Price', 'Item URL'])
                        matched_df = pd.DataFrame(matched_results, columns=['Fooza Food Name', 'Fooza Price', 'Swiggy Food Name', 'Swiggy Price', 'Zomato Food Name', 'Zomato Price', 'Item URL'])
                        #matched_df=int(matched_df['Fooza Food Name'].round(0))
                        # Function to apply conditional highlighting
                        def highlight_mismatches(row):
                            highlight = 'background-color: #89CFF0;'
                            default = ''
                            
                            # Highlight 'Fooza Food Name' if the item name does not match with Swiggy or Zomato
                            fooza_name_highlight = highlight if row['Swiggy Food Name'] == "Not Matching" or row['Zomato Food Name'] == "Not Matching" else default
                            
                            # Check if 'Fooza Price' is numeric and convert to integer, otherwise highlight as a mismatch
                            try:
                                fooza_price = int(row['Fooza Price'])
                            except ValueError:
                                fooza_price = None
                                fooza_name_highlight = highlight  # Highlight 'Fooza Food Name' if price is not valid
                        
                            # Initialize highlights for Swiggy and Zomato prices as default
                            swiggy_price_highlight = default
                            zomato_price_highlight = default
                            
                            # Highlight 'Swiggy Price' if there is a price difference and it's a valid number
                            if fooza_price is not None and row['Swiggy Food Name'] != "Not Matching":
                                try:
                                    swiggy_price = int(row['Swiggy Price'])
                                    if fooza_price != swiggy_price:
                                        swiggy_price_highlight = highlight
                                except ValueError:
                                    swiggy_price_highlight = highlight  # Highlight if Swiggy price is not a number
                            
                            if fooza_price is not None and row['Zomato Food Name'] != "Not Matching":
                                try:
                                    zomato_price = int(row['Zomato Price'])
                                    if fooza_price != zomato_price:
                                        zomato_price_highlight = highlight
                                except ValueError:
                                    zomato_price_highlight = highlight  # Highlight if Zomato price is not a number or if ₹ symbol removal fails
                        
                            # Return the appropriate highlights for each column
                            return [fooza_name_highlight, default, default, swiggy_price_highlight, default, zomato_price_highlight, default]
                                                                       
                        def format_price(value):
                            # Format the price to two decimal places if needed, otherwise as an integer
                            return f"{value:.2f}".rstrip('0').rstrip('.') if '.' in f"{value:.2f}" else f"{value:.2f}"
                        
                        # Apply the highlighting to the DataFrame
                        styled_df = matched_df.style.apply(highlight_mismatches, axis=1).format({'Fooza Price': format_price})
                        # Display the styled DataFrame
                        #styled_df
                        st.write(styled_df)
                        
                        import openpyxl
                        import os
                        
                        
                        matched_items_with_urls = styled_df
                        f_deta=merged_df['name'][0] + ', ' +merged_df['location'][0]
                        # Section 2: Restaurant Details
                        restaurant_details = pd.DataFrame({
                            'Source': ['Fooza', 'Swiggy', 'Zomato'],
                            'Item Count': [len(filtered_df), len(dfs), len(df_zomato)],
                            'Restaurant Name':[f_deta,s_deta,z_deta]
                        })
                        
                        # Section 3: Unmatched Items
                        unmatched_swiggy = dfs[~dfs['Item Name'].isin(matched_df['Swiggy Food Name'])][['Item Name', 'Item Price']].rename(columns={'Item Name': 'Swiggy Item', 'Item Price': 'Swiggy Price'})
                        unmatched_zomato = df_zomato[~df_zomato['Item Name'].isin(matched_df['Zomato Food Name'])][['Item Name', 'Item Price']].rename(columns={'Item Name': 'Zomato Item', 'Item Price': 'Zomato Price'})
                        unmatched_items = pd.concat([unmatched_swiggy.reset_index(drop=True), unmatched_zomato.reset_index(drop=True)], axis=1)
                        
                        # Section 4: Complete Item List
                        complete_item_list = pd.concat([
                            filtered_df[['food_item', 'selling_price']].rename(columns={'food_item': 'Fooza Item', 'selling_price': 'Fooza Price'}),
                            dfs[['Item Name', 'Item Price']].rename(columns={'Item Name': 'Swiggy Item', 'Item Price': 'Swiggy Price'}),
                            df_zomato[['Item Name', 'Item Price']].rename(columns={'Item Name': 'Zomato Item', 'Item Price': 'Zomato Price'})
                        ], axis=1)
                        
                        output = BytesIO()

                        # Write to Excel in memory
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            matched_items_with_urls.to_excel(writer, sheet_name='Matched Items', index=False)
                            restaurant_details.to_excel(writer, sheet_name='Restaurant Details', index=False)
                            unmatched_items.to_excel(writer, sheet_name='Unmatched Items', index=False)
                            complete_item_list.to_excel(writer, sheet_name='Complete Item List', index=False)
                        
                        # Seek to the beginning of the BytesIO object
                        output.seek(0)
                        
                        # Create a download button and offer the file to the user
                        btn = st.download_button(
                                label="Download Excel File",
                                data=output,
                                file_name=f"{y}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        
                        if btn:
                            st.success('File has been downloaded successfully!')
                        
                        
                        
                        
                        import smtplib
                        from email.mime.multipart import MIMEMultipart
                        from email.mime.text import MIMEText
                        from email.mime.base import MIMEBase
                        from email.mime.image import MIMEImage
                        from email import encoders
                        
                        
                        # Assuming 'merged_df' is your DataFrame with the restaurant information
                        # Assuming 'y' is a unique identifier for the email attachment filename
                        
                        # Path to your image and Excel file
                        image_path = 'static/fooza.png'
                        
                        sender_email = 'sysadmin@fooza.in'
                        password = 'wvitiiaebtvwtffl'
                        # Setup the MIME
                        message = MIMEMultipart('related')
                        message['From'] = 'Fooza Foods Private Limited <sysadmin@fooza.in>'
                        message['To'] = 'khurram.shakoor@fooza.in'
                        message['Subject'] = '{} Price Validation Fooza'.format(merged_df['ResName'][0])
                        recipients = ['mdkhurram786@gmail.com', 'khurramer2018@gmail.com']
                        message['Cc'] = ', '.join(recipients)
                        
                        # Read the image data
                        with open(image_path, 'rb') as img_file:
                            msg_image = MIMEImage(img_file.read())
                            msg_image.add_header('Content-ID', '<fooza_image>')  # Use '<fooza_image>' as the Content-ID
                        
                        # HTML body with embedded image and dynamic data from the DataFrame
                        html_body = f"""
                        <html>
                          <body>
                            <img src="cid:fooza_image" alt="Fooza Logo" style="width:200px;height:100px;"><br>
                            <h2 style="color: #4A90E2;">Restaurant Price validation for Fooza</h2>
                            <p>Hello {merged_df['RM'][0]},</p>
                            <p>We hope this message finds you well. Please verify the attachment for price validation from different platforms.</p>
                            <table style="border-collapse: collapse; width: 100%;">
                              <tr>
                                <td style="border: 1px solid #dddddd; text-align: left; padding: 8px;">Restaurant ID</td>
                                <td style="border: 1px solid #dddddd; text-align: left; padding: 8px;">{merged_df['id'][0]}</td>
                              </tr>
                              <tr>
                                <td style="border: 1px solid #dddddd; text-align: left; padding: 8px;">Restaurant Name</td>
                                <td style="border: 1px solid #dddddd; text-align: left; padding: 8px;">{merged_df['ResName'][0]}</td>
                              </tr>
                              <tr>
                                <td style="border: 1px solid #dddddd; text-align: left; padding: 8px;">Restaurant POS</td>
                                <td style="border: 1px solid #dddddd; text-align: left; padding: 8px;">{merged_df['restaurant_pos'][0]}</td>
                              </tr>
                              <tr>
                                <td style="border: 1px solid #dddddd; text-align: left; padding: 8px;">Partner Name</td>
                                <td style="border: 1px solid #dddddd; text-align: left; padding: 8px;">{merged_df['PartnerName'][0]}</td>
                              </tr>
                              <tr>
                                <td style="border: 1px solid #dddddd; text-align: left; padding: 8px;">Partner Number</td>
                                <td style="border: 1px solid #dddddd; text-align: left; padding: 8px;">{merged_df['phone_number'][0]}</td>
                              </tr>
                              <tr>
                                <td style="border: 1px solid #dddddd; text-align: left; padding: 8px;">Restaurant Mode</td>
                                <td style="border: 1px solid #dddddd; text-align: left; padding: 8px;">{merged_df['ResMode'][0]}</td>
                              </tr>
                              <tr>
                                <td style="border: 1px solid #dddddd; text-align: left; padding: 8px;">No of Fooza Items</td>
                                <td style="border: 1px solid #dddddd; text-align: left; padding: 8px;">{len(filtered_df)}</td>
                              </tr>
                              <tr>
                                <td style="border: 1px solid #dddddd; text-align: left; padding: 8px;">No of swiggy Items</td>
                                <td style="border: 1px solid #dddddd; text-align: left; padding: 8px;">{len(dfs)}</td>
                              </tr>
                              <tr>
                                <td style="border: 1px solid #dddddd; text-align: left; padding: 8px;">No of Zomato Items</td>
                                <td style="border: 1px solid #dddddd; text-align: left; padding: 8px;">{len(df_zomato)}</td>
                              </tr>
                              
                            </table>
                            <p>This change may have an impact on your operations.</p>
                            <p>Thank you for connecting with Fooza.</p>
                            <a href="https://fooza.in/">Visit Fooza.in</a>
                          </body>
                        </html>
                        """
                        
                        # Attach the HTML body and image to the email
                        message.attach(MIMEText(html_body, 'html'))
                        message.attach(msg_image)
                        
                        # Open the Excel file to attach to the email
                        part = MIMEBase('application', 'octet-stream')
                        # Set the payload to the read contents of the BytesIO object
                        part.set_payload(output.getvalue())
                        encoders.encode_base64(part)
                        # Set the filename to the desired name
                        part.add_header('Content-Disposition', f'attachment; filename="{y}.xlsx"')
                        message.attach(part)

                        
                        # Send the email
                        try:
                           server = smtplib.SMTP('smtp.gmail.com', 587)
                           server.starttls()
                           server.login(sender_email, password)
                           server.sendmail(sender_email, [message['To']] + recipients, message.as_string())
                           server.quit()
                           st.subheader('Email sent successfully!')
                        except Exception as e:
                           st.subheader(f'Failed to send email: {e}')              
    
    
    
    
                        
    
    
    
    
    
    
            
            
            
            
            
            
            
        
        

if __name__ == '__main__':
    main()









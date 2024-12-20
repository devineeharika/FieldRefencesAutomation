import requests
import streamlit as st
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
import time
import pandas as pd
from selenium.webdriver.common.by import By
from multiprocessing import Pool, Manager
import constants
import csv
import multiprocessing


from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service


def get_salesforce_sid(username, password, security_token, LOGIN_URL):
    """
    Log in to Salesforce using the SOAP API to retrieve the SID.
    """
    headers = {
        "Content-Type": "text/xml; charset=UTF-8",
        "SOAPAction": "login"
    }
    
    # SOAP Request Body
    soap_body = f"""
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                      xmlns:urn="urn:partner.soap.sforce.com">
       <soapenv:Header/>
       <soapenv:Body>
          <urn:login>
             <urn:username>{username}</urn:username>
             <urn:password>{password}{security_token}</urn:password>
          </urn:login>
       </soapenv:Body>
    </soapenv:Envelope>
    """
    
    response = requests.post(LOGIN_URL, data=soap_body, headers=headers)
    if response.status_code != 200:
        print("Error during login:", response.text)
        return None

    # Extract SID and Server URL from the response
    from xml.etree import ElementTree as ET
    root = ET.fromstring(response.content)
    sid = root.find(".//{urn:partner.soap.sforce.com}sessionId").text
    server_url = root.find(".//{urn:partner.soap.sforce.com}serverUrl").text
    
    return sid, server_url

def process_url(driver, url, page_data,field,failed_urls_data):
    try:
        
        page_data_file_path = constants.page_data_file_path
        count = 0
        driver.switch_to.frame(0)
        ele = driver.find_element(By.XPATH, "//h2[@class='pageDescription']")
        print(f"Page Description for {url}: {ele.text}")       
        whr_btn = driver.find_element(By.XPATH, "//input[@title='Where is this used?']")
        whr_btn.click()
        print("Button clicked for URL:", url)       
        time.sleep(10)
        driver.switch_to.default_content()
        time.sleep(10)
        driver.switch_to.frame(0)       
        table = driver.find_element(By.XPATH, "//table[@class='list']/tbody")
        rows_list = table.find_elements(By.TAG_NAME, "tr")       
        for row in rows_list:
            row_head_list = row.find_elements(By.TAG_NAME, "th")
            data_list = row.find_elements(By.TAG_NAME, "td")           
            for head in row_head_list:
                if head.text != "Reference Type" and head.text != "Reference Label":
                    page_data['Reference Type'].append(head.text)
                    count = count+1 
                    print(head.text + " ,", end="")
            for data in data_list:
                try:
                    link_element = data.find_element(By.TAG_NAME, "a")
                    link_text = link_element.text
                    page_data['Reference Label'].append(link_text)
                    page_data['Reference Label URL'].append("")
                    print(link_text + " ,", end="")   

                except Exception:
                    link_text = data.text
                    page_data['Reference Label'].append(link_text)
                    page_data['Reference Label URL'].append('')
                    print(link_text + " ,", end="")   
            print()
        print(count,field)
        page_data['Field Name'].extend([field] * count) 
        page_data = pd.DataFrame(page_data)
        page_data.to_csv(page_data_file_path, mode='a', index=False, header=not pd.io.common.file_exists(page_data_file_path))
    except Exception as e:
        failed_urls_data["Url"].append(url)
        failed_urls_data["Error"].append(str(e))
        failed_urls_data["Page"].append("Second")
        failed_urls_data = pd.DataFrame(failed_urls_data)
        failed_urls_data.to_csv(constants.failed_urls_file_path, mode='a', index=False, header=not pd.io.common.file_exists(constants.failed_urls_file_path))
        print(f"Error processing URL {url}: {str(e)}")
    

def get_first_page_details(driver, page_url, first_page_data, failed_urls_data):
    try:
        first_page_file_path = constants.first_page_file_path
        
        driver.switch_to.frame(0)
        time.sleep(2)
        try:
            ele = driver.find_element(By.XPATH, "//*[@id='ep']/div[2]/div[3]/table/tbody/tr[1]/td[1]").text
            if ele == 'Field Label':
                table = driver.find_element(By.XPATH, "//*[@id='ep']/div[2]/div[3]/table/tbody")  
        except Exception:
            ele = driver.find_element(By.XPATH, "//*[@id='ep']/div[2]/div[4]/table/tbody/tr[1]/td[1]").text 
            if ele == 'Field Label':
                table = driver.find_element(By.XPATH, "//*[@id='ep']/div[2]/div[4]/table/tbody")
 
        rows_list = table.find_elements(By.TAG_NAME, "tr")       
        for row in rows_list:
            rows_list = row.find_elements(By.TAG_NAME, "td")
            if len(rows_list) >= 4:
                if rows_list[2].text in first_page_data:
                    first_page_data[rows_list[2].text].append(rows_list[3].text)
                if rows_list[0].text in first_page_data:
                    first_page_data[rows_list[0].text].append(rows_list[1].text)
                    time.sleep(2)
            elif len(rows_list) >= 2:
                if rows_list[0].text in first_page_data:
                    first_page_data[rows_list[0].text].append(rows_list[1].text)
        time.sleep(2)
        print("first page details --", first_page_data) 
        first_page_data = pd.DataFrame(first_page_data)
        first_page_data.to_csv(first_page_file_path, mode='a', index=False, header=not pd.io.common.file_exists(first_page_file_path))
        driver.switch_to.default_content() 
    except Exception as e:
        failed_urls_data["Url"].append(page_url)
        failed_urls_data["Error"].append(str(e))
        failed_urls_data["Page"].append("First")
        failed_urls_data = pd.DataFrame(failed_urls_data)
        failed_urls_data.to_csv(constants.failed_urls_file_path, mode='a', index=False, header=not pd.io.common.file_exists(constants.failed_urls_file_path))
        print(f"Error processing URL {page_url}: {str(e)}")
    



def chunk_urls(urls, num_chunks):
    """Divide URLs into specified number of chunks."""
    avg = len(urls) // num_chunks
    chunks = [urls[i * avg:(i + 1) * avg] for i in range(num_chunks)]
    if len(urls) % num_chunks != 0:  # Handle remaining URLs
        chunks[-1].extend(urls[num_chunks * avg:])
    return chunks       

def login_with_sid_in_browser(browser, sid, instance_url):
    """
    Log in to Salesforce using the retrieved SID in a browser.
    """

    if browser.lower() == "chrome":
        options = webdriver.ChromeOptions()
    
        options.add_argument('--disable-gpu')
        options.add_argument('--headless')
        
        service = Service()
        driver = webdriver.Chrome(service=service, options=options)
    elif browser.lower() == "firefox":
        driver = webdriver.Firefox(service=FirefoxService())
    else:
        raise ValueError("Invalid browser name. Use 'chrome' or 'firefox'.")
    try:
        # Construct the frontdoor.jsp URL
        login_url = f"{instance_url.split('/services')[0]}/secur/frontdoor.jsp?sid={sid}"
        driver.get(login_url)
        driver.maximize_window()
        print("Logged in successfully using SID in browser.")
    except Exception as e:
        print("Logged in Failed using SID in browser- {str(e)}")
    return driver


def empty_dicts():
    page_data = {
        "Reference Type": [],
        "Reference Label": [],
        "Field Name": [],
        "Reference Label URL": []
    }
    first_page_data = {
        "Field Label": [],
        "Object Name": [],
        "Field Name": [],
        "API Name": [],
        "Description": []
    }
    failed_urls_data = {
        "Url": [],
        "Error": [],
        "Page": [], #First page(First) or Second page(Second).
    }
    return page_data,first_page_data,failed_urls_data

def process_url_chunk_with_progress(instance_url, chunk, file_path, sid, progress_queue, chunk_size):
    """
    Process a chunk of URLs, scrape data, and update shared progress in real-time.
    """
    driver = login_with_sid_in_browser("chrome", sid, instance_url)
    print("started drivers")
    try:
                
        total_urls = len(chunk)
        for index, i in enumerate(chunk):
            
            page_data,first_page_data,failed_urls_data = empty_dicts()
            
            # Simulate processing time
            time.sleep(1)

            # Process the URL and update data
            dataframe = pd.read_csv(file_path)
            page_url = f"{instance_url.split('/services')[0]}/lightning/setup/ObjectManager/{dataframe['DurableId'][i].split('.')[0]}/FieldsAndRelationships/{dataframe['DurableId'][i].split('.')[1]}/view"
            print(f"Processing URL: {page_url}")
            driver.get(page_url)
            time.sleep(10)
            
            get_first_page_details(driver, page_url, first_page_data, failed_urls_data)
            page_data,first_page_data,failed_urls_data = empty_dicts()
            time.sleep(2)
            process_url(driver, page_url, page_data, dataframe['QualifiedApiName'][i], failed_urls_data)
            
            # Send progress update to the main thread
            progress_queue.put(1)  # Increment progress by 1 for each processed URL

        

    except Exception as e:
        if i < len(chunk):
            failed_urls_data = {
                "Url": [],
                "Error": [],
                "Page": [], #First page(First) or Second page(Second).
            }
            for i in range(len(chunk)):
                dataframe = pd.read_csv(file_path)
                page_url = f"{instance_url.split('/services')[0]}/lightning/setup/ObjectManager/{dataframe['DurableId'][i].split('.')[0]}/FieldsAndRelationships/{dataframe['DurableId'][i].split('.')[1]}/view"           
                failed_urls_data["Url"].append(page_url)
                failed_urls_data["Error"].append(str(e))
                failed_urls_data["Page"].append("Initial")
            failed_urls_data = pd.DataFrame(failed_urls_data)
            failed_urls_data.to_csv(constants.failed_urls_file_path, mode='a', index=False, header=not pd.io.common.file_exists(constants.failed_urls_file_path))
        print(f"Error processing URL chunk: {e}")
    finally:
        driver.quit()



def get_details_with_multiprocessing_and_progress(instance_url, file_path, num_processes, sid):
    """
    Process URLs using multiprocessing for parallel execution and show progress in real-time.
    """
    dataframe = pd.read_csv(file_path)
    num_urls = len(dataframe['DurableId'])
    page_data_file_path = constants.page_data_file_path
    first_page_file_path = constants.first_page_file_path
    failed_urls_file_path = constants.failed_urls_file_path
    if os.path.exists(page_data_file_path):
        os.remove(page_data_file_path)
    if os.path.exists(first_page_file_path):
        os.remove(first_page_file_path)
    if os.path.exists(failed_urls_file_path):
        os.remove(failed_urls_file_path)

    # Create chunks of indices
    chunks = chunk_urls(list(range(num_urls)), num_processes)

    # Create a queue to communicate progress
    progress_queue = Manager().Queue()

    st.write("### progress bar:")
    # Initialize progress bar
    progress_bar = st.progress(0)

    # Start multiprocessing pool
    with Pool(processes=num_processes) as pool:
        # Start processing chunks
        for chunk in chunks:
            pool.apply_async(process_url_chunk_with_progress, 
                                     (instance_url, chunk, file_path, sid, progress_queue, len(chunk)))
            

        # Continuously update the progress bar
        total_processed = 0
        while total_processed < num_urls:
            # Check if there's any progress update in the queue
            if not progress_queue.empty():
                # Update the progress count
                total_processed += progress_queue.get()
                progress_bar.progress(total_processed / num_urls)  # Update progress bar
        
        # Wait for all processes to finish
        pool.close()
        pool.join()


  

# Main function to log in and open Salesforce in a browser
def main():
    
    # Load the Salesforce logo
    salesforce_logo = constants.salesforce_logo_image

    # Display the Salesforce logo at the top
    st.markdown(
        f"""
        <div style="text-align: center;">
            <img src="{salesforce_logo}" alt="Salesforce Logo" width="200">
        </div>
        """,
        unsafe_allow_html=True,
    )

    # App title
    st.title("Salesforce Login & File Upload")

    # Input fields for Salesforce login credentials
    st.subheader("Enter Your Salesforce Credentials:")
    username = st.text_input("Username", placeholder="Enter your Salesforce username")
    password = st.text_input("Password", placeholder="Enter your Salesforce password", type="password")
    security_token = st.text_input("Security Token", placeholder="Enter your Salesforce security token")
    LOGIN_URL = st.text_input("LOGIN URL", placeholder="Enter your LOGIN URL")

    # # Salesforce SOAP Login URL
    # LOGIN_URL = "https://login.salesforce.com/services/Soap/u/57.0"  # Replace `57.0` with your API version if needed.
    # LOGIN_URL = "https://test.salesforce.com/services/Soap/u/57.0"  # Replace `57.0` with your API version if needed.

    # File upload
    st.subheader("Upload a File:")
    uploaded_file = st.file_uploader("Choose a file", type=["csv", "txt", "json", "xml"])

    # Create a directory to store files locally
    os.makedirs(constants.uploaded_file_folder, exist_ok=True)

    # Submit button
    if st.button("Submit"):
        if username and password and security_token and uploaded_file:
            
            # Save the uploaded file
            file_path = os.path.join("uploaded_files", uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.success("Credentials and file uploaded and stored successfully!")
            st.write("### Uploaded File Details:")
            st.write(f"**Filename:** {uploaded_file.name}")
            st.write(f"**File Path:** {file_path}")
            st.write(f"**File Type:** {uploaded_file.type}")
            st.write(f"**File Size:** {uploaded_file.size} bytes")
            # Get SID and Server URL
            sid, instance_url = get_salesforce_sid(username, password, security_token, LOGIN_URL)
            if sid:
                print("Successfully retrieved SID:", sid)
                print("Instance URL:", instance_url)
                
                # Use SID to log in via browser
                # driver = login_with_sid_in_browser("chrome", sid, instance_url)
                # time.sleep(10000)
                # get_first_page_details(driver, instance_url, file_path)
                # get_details_from_url(instance_url, file_path, driver)
                num_processes = constants.num_processes  # Adjust the number of processes based on your system
                start_time = time.time()  
                get_details_with_multiprocessing_and_progress(instance_url, file_path, num_processes, sid)
                end_time = time.time()   
                st.success("Successfully Extracted data and stored in CSV files.")
                # Calculate elapsed time in minutes
                elapsed_time_minutes = (end_time - start_time) / 60
                st.write(f"**Total time taken:** {elapsed_time_minutes:.2f} minutes.")
                
            else:
                print("Failed to retrieve SID.")
        else:
            st.error("Please fill in all fields and upload a file.")

    # Footer
    st.markdown(
        """
        <hr>
        <p style="text-align: center;">Powered by <b>Streamlit</b></p>
        """,
        unsafe_allow_html=True,
    )

        

# Run the script
if __name__ == "__main__":
    main()








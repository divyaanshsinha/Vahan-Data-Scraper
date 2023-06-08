import time, sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
import csv


filename = "rto_file.csv"
url = 'https://vahan.parivahan.gov.in/vahan4dashboard/vahan/view/reportview.xhtml'
refresh_button_id = "j_idt63"


### Helper tools ###
def init_webdriver():
    # --- Options to make scraping faster
    options = Options()
    options.add_argument("--disable-extensions")
    options.add_argument("--headless")
    options.add_argument("--allow-insecure-localhost")
    driver = webdriver.Chrome(options=options, service=Service(ChromeDriverManager().install()))
    return driver

# Identifies element to be clicked by id, waits for element to be clickable for 
# at most 10s and then clicks. If it takes too long (elem doesn't exist or 
# rendering takes too long) then sys exits 
def safe_click_by_id(id : str):
    try:
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, id))).click()
    except TimeoutException:
        print(TimeoutException)
        print(id)
        sys.exit()

def choose_elem_from_dropdown(dropdownID, elemID):
    safe_click_by_id(dropdownID)
    # Might be better to search by text than by id for long-term stability
    # I don't know how yet
    safe_click_by_id(elemID)
    safe_click_by_id(dropdownID)

# Clicks refresh button
def refresh():
    safe_click_by_id(refresh_button_id)



### Functions that interact with the website ###
#Starts up the actual page
def init_page():
    driver = init_webdriver()
    driver.get(url)
    return driver

# Extracting data from dropdown menu names to enter into csv
# This is a simple interpreter, requiring menu names to be 
# of the expected format
def RTO_label_interpreter(label):
    RTO_details = label.split(" - ")

    # Dealing with exceptions where RTO's have " - " in their names
    if len(RTO_details) > 2:
        name = RTO_details[0]
        for idx in range(1, len(RTO_details)-1):
            name = name + " - " + RTO_details[idx]
        RTO_details = [name, RTO_details[-1]]

    RTO_name = RTO_details[0]
    end_index = RTO_details[1].find('(')
    if end_index == -1:
        print("RTO naming format changed in dropdown menu")
        print(RTO_details)
        sys.exit()
    state_code = RTO_details[1][0:2]
    RTO_code = RTO_details[1][2:end_index]

    return RTO_name, state_code, RTO_code

#Loops through every rto for a chosen state
def get_rto_codes(state_name):
    rto_select = Select(driver.find_element(by=By.ID, value="selectedRto_input"))
    #This includes the 0th option which we don't want
    num_rto_options = len(rto_select.options)
    #Loop through the relevant options in the RTO dropdown menu
    for idx in range(1, num_rto_options):
        opt = rto_select.options[idx]
        RTO_label = opt.get_attribute("text")

        RTO_name, state_code, RTO_code = RTO_label_interpreter(RTO_label)

        # To be entered into csv
        data = [state_name, RTO_name, state_code, RTO_code]

        csvfile = open(filename, 'a', newline='')
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(data)
        csvfile.close()

#Loops through all available states in the dropdown menu
def state():
    state_select = Select(driver.find_element(by=By.ID, value="j_idt33_input"))
    #This includes the 0th option which we don't want
    num_state_options = len(state_select.options)
    #Loop through the relevant options in the state dropdown menu
    for idx in range(1, num_state_options):
        state_label = state_select.options[idx].get_attribute('text')
        state_name = state_label[:state_label.find('(')]
        choose_elem_from_dropdown("j_idt33", f"j_idt33_{idx}")
        time.sleep(5)
        get_rto_codes(state_name)
        refresh()
        continue


def main():
    fields = ['State', 'RTO', 'State Code', 'RTO Code']

    csvfile = open(filename, 'w', newline='')
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(fields)
    csvfile.close()

    global driver
    driver = init_page()
    state()
    time.sleep(1)
    return True

if __name__ == "__main__":
    main()
import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import helper

url = 'https://vahan.parivahan.gov.in/vahan4dashboard/vahan/view/reportview.xhtml'
curr_viewstate = None
data = {'key':'value'}
# The desired field for the csv
fields = ['State', 'RTO', 'Year', 'Month', 'Vehicle Category', 
          'Electric Vehicles']
filename = "vahan_data.csv"

# The payloads were obtained by manually navigating the pages, and seeing what
# payloads were sent to the server on each click, noticing a pattern 
# (the relevant fields are commented on below), and copying the payload

# By right, all 3  payloads below should have the line:
# javax.faces.partial.ajax: true
# but deleting this line forces the response to contain the code for the entire
# webpage and not just the updated elements, allowing us to easily parse the
# entire page and the data inside.

# Payload for choosing a state, so that the corresponding RTO menu is rendered
payload_for_rto_dropdown = {
    # The source for the page change is clicking 
    # on the state dropdown with HTML id j_idt33
    "javax.faces.source": "j_idt33",
    "javax.faces.partial.execute": "j_idt33",
    # Choosing a state causes the relevant RTO menu with 
    # id selectedRto to be rendered 
    "javax.faces.partial.render": "selectedRto",
    "javax.faces.behavior.event": "change",
    "javax.faces.partial.event": "change",
    "masterLayout_formlogin": "masterLayout_formlogin",
    "j_idt24_focus": "",
    "j_idt24_input": "A",
    "j_idt33_focus": "", 
    # Value here indicates which state we want to look at, the value should be
    # the State code from rto_file.csv. -1 indicates the choice of all states
    # (First choice in the state dropdown menu)
    "j_idt33_input": "",
    "selectedRto_focus": "",
    # Value here indicates which RTO we want to look at, the value should be
    # the RTO code from rto_file.csv. -1 indicates the choice of all RTO
    # (First choice in the RTO dropdown menu) Should not be -1 only if a state
    # code is provided in j_idt33_input
    "selectedRto_input": -1,
    "yaxisVar_focus": "", 
    # The yAxis input
    "yaxisVar_input": "Vehicle Category",
    "xaxisVar_focus": "",
    # The xAxis input
    "xaxisVar_input": "Fuel",
    "selectedYearType_focus": "",
    # Year type, C indicates in calendar year
    "selectedYearType_input": "C",
    "selectedYear_focus": "", 
    "selectedYear_input": 2022,
    "groupingTable:selectMonth_focus": "",
    # Which month of the year to look at on the month dropdown
    # Ex: 2022 indicates data for the whole year, 
    #     202201 indicates data for Jan 2022
    "groupingTable:selectMonth_input": 2022,
    "vchgroupTable_scrollState": "0,0",
    "javax.faces.ViewState": curr_viewstate
}

# Payload that refreshes the page with the relevant parameters
payload_for_refreshing = {
        # The source of changes was clicking the refresh button with id j_idt63
        "javax.faces.source": "j_idt63",
        "javax.faces.partial.execute": "@all",
        "javax.faces.partial.render": "VhCatg+norms+fuel+VhClass+combTablePnl+groupingTable+msg+vhCatgPnl",
        "j_idt63": "j_idt63",
        "masterLayout_formlogin": "masterLayout_formlogin",
        "j_idt24_focus": "",
        "j_idt24_input": "A",
        "j_idt33_focus": "", 
        "j_idt33_input": -1,
        "selectedRto_focus": "",
        "selectedRto_input": -1,
        "yaxisVar_focus": "", 
        "yaxisVar_input": "Vehicle Category",
        "xaxisVar_focus": "", 
        "xaxisVar_input": "Fuel",
        "selectedYearType_focus": "", 
        "selectedYearType_input": "C",
        "selectedYear_focus": "", 
        "selectedYear_input": 2022,
        "groupingTable:selectMonth_focus": "", 
        "groupingTable:selectMonth_input": 2022,
        "vchgroupTable_scrollState": "0,0",
        "javax.faces.ViewState": curr_viewstate
    }

# Payload to choose the correct month, to be used after the page for 
# an RTO is selected
payload_for_monthly_data = {
        # The source of changes was clicking on the select month button, 
        # after the page yearly page for the RTO is loaded,
        # with id groupingTable:selectMonth
        "javax.faces.source": "groupingTable:selectMonth",
        "javax.faces.partial.execute": "groupingTable:selectMonth",
        "javax.faces.partial.render": "combTablePnl",
        "javax.faces.behavior.event": "change",
        "javax.faces.partial.event": "change",
        "masterLayout_formlogin": "masterLayout_formlogin",
        "j_idt24_focus": "",
        "j_idt24_input": "A",
        "j_idt33_focus": "", 
        "j_idt33_input": -1,
        "selectedRto_focus": "",
        "selectedRto_input": -1,
        "yaxisVar_focus": "", 
        "yaxisVar_input": "Vehicle Category",
        "xaxisVar_focus": "", 
        "xaxisVar_input": "Fuel",
        "selectedYearType_focus": "", 
        "selectedYearType_input": "C",
        "selectedYear_focus": "", 
        "selectedYear_input": 2022,
        "groupingTable:selectMonth_focus":"", 
        "groupingTable:selectMonth_input": 202201,
        "vchgroupTable_scrollState": "0,0",
        "javax.faces.ViewState": curr_viewstate
    }

### Basic helper Functions ###
def get_viewstate_from_response(response):
    soup = BeautifulSoup(response.content, "html.parser")
    viewstate_elem = soup.find(id="j_id1:javax.faces.ViewState:0")
    return viewstate_elem['value']

# Loads page using a post request, when given a session and a payload
def load_page(session, payload):
    return session.post(url, data = payload)

# For debugging. Writes to a file which can then be opened in a browser
# so that the page we are on can be visualized
def write_for_display(response):
    with open('file.html', mode = 'w') as file:
        for line in response.text:
            file.write(line)



### Major helper functions ###
# Writes data from table in the response to the csv
# Simple interpreter that requires the data be of a certain format
def table_to_csv_data(state, rto, year, month, response):
    csvfile = open(filename, 'a', newline='')

    soup = BeautifulSoup(response.content, "html.parser")
    table_body= soup.find(id="groupingTable_data")
    table_rows = table_body.find_all('tr')
    
    for row in table_rows:
        cols = row.find_all('td')
        if len(cols) == 1 and len(table_rows) == 1:
            if cols[0].get_text() != "No records found.":
                print("Table format unexpected")
                print(state, rto)
                exit()
        else:
            vehicle_cat = cols[1].get_text()
            num_EVs = cols[9].get_text()

            csvwriter = csv.writer(csvfile)
            csv_data = [state, rto, year, month, vehicle_cat, num_EVs]
            csvwriter.writerow(csv_data)

    csvfile.close()      


# Scrapes data for the given rto, and year specified until the month specified
def scrape_data(rto_info, month_until, year):

    # Load the initial webpage
    response = session.get(url,data=data)
    state = rto_info[0]; rto = rto_info[1] 
    state_code = rto_info[2]; rto_code = rto_info[3]
    
    # Inital POST request to fix xAxis to Fuel, yAxis to Vehicle Category, 
    # and set the year value
    # Every time we call load_page after the initial get request, we send the viewstate
    # from the previous response in the payload we are about to send 
    curr_viewstate = get_viewstate_from_response(response)
    payload_for_refreshing['javax.faces.ViewState'] = curr_viewstate
    payload_for_refreshing["selectedYear_input"] = year
    payload_for_refreshing["groupingTable:selectMonth_input"] = year
    response = load_page(session, payload_for_refreshing)

    # POST request format to select the state, 
    # and render the corresponding RTO dropdown menu
    curr_viewstate = get_viewstate_from_response(response)
    payload_for_rto_dropdown["j_idt33_input"] = state_code
    payload_for_rto_dropdown['javax.faces.ViewState'] = curr_viewstate
    response = load_page(session, payload_for_rto_dropdown)
        
    # POST request to render table corresponding to the RTO
    curr_viewstate = get_viewstate_from_response(response)
    payload_for_refreshing["j_idt33_input"] = state_code
    payload_for_refreshing["selectedRto_input"] = rto_code
    payload_for_refreshing['javax.faces.ViewState'] = curr_viewstate
    response = load_page(session, payload_for_refreshing)

    # POST request to choose the month for the given RTO
    curr_viewstate = get_viewstate_from_response(response)
    payload_for_monthly_data["j_idt33_input"] = state_code
    payload_for_monthly_data["selectedYear_input"] = year
    payload_for_monthly_data["selectedRto_input"] = rto_code
    payload_for_monthly_data['javax.faces.ViewState'] = curr_viewstate

    for month in range(1, month_until+1):
        # Load the page and it's table for each month and write to csv
        month_input = year*100 + month
        payload_for_monthly_data["groupingTable:selectMonth_input"] = month_input
        response = load_page(session, payload_for_monthly_data)
        table_to_csv_data(state, rto, year, month, response)

# Writes the initial header after clearing any current data from 
# the vahan_data.csv file
def init_csv():
    csvfile = open(filename, 'w', newline='')
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(fields)
    csvfile.close()

def main():
    # Update list of all RTOs by state and their respective codes
    # Lists all current states, and their RTOs by name and code
    # in rto_file.csv
    #--- helper.main()

    # WILL OVERWRITE vahan_data.cv FILE IN THE SAME FOLDER, IF ANY
    #--- init_csv()

    month = datetime.now().month
    year = datetime.now().year

    # The year until which to scrape data
    year_until = -1
    if month == 1:
        year_until = year - 1
    else:
        year_until = year

    rto_data_csv = open("rto_file.csv")
    header = next(rto_data_csv)

    all_rto_info = csv.reader(rto_data_csv)
    line_num = 1

    global session
    with requests.session() as session:
        for rto_info in all_rto_info:
            for year in range(2022, year_until+1):
                if datetime.now().year != year:
                    month_until = 12
                else:
                    if datetime.now().month == 1:
                        raise Exception("It is January, we should not be scraping data for this year")
                    else:
                        month_until = datetime.now().month-1
                scrape_data(rto_info, month_until, year)
    
    rto_data_csv.close()

if __name__ == "__main__":
    main()
import os
import subprocess
import requests
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.mouse_button import MouseButton
from selenium import webdriver
from selenium.webdriver.chromium.options import ChromiumOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import time
import argparse
import pandas as pd

class Colors:
    RESET = "\033[0m"
    BLACK = "\033[30m"
    ORANGE = "\033[33m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

# MLX API variables
MLX_BASE = "https://api.multilogin.com"
MLX_LAUNCHER = "https://launcher.mlx.yt:45001/api/v1"
LOCALHOST = "http://127.0.0.1"
HEADERS = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

list=[]

parser = argparse.ArgumentParser(description='Process data based on form input.')
parser.add_argument('--number', type=int, help='Number of keywords')
parser.add_argument('--keywords', type=str, help='Keywords separated by comma')
parser.add_argument('--email', type=str, help='Keywords separated by comma')
parser.add_argument('--password', type=str, help='Keywords separated by comma')
parser.add_argument('--profileid', type=str, help='Keywords separated by comma')
parser.add_argument('--folderid', type=str, help='Keywords separated by comma')

args = parser.parse_args()

number_of_keywords = args.number
keywords = args.keywords.split(',') if args.keywords else []
username = args.email
password = args.password
profile_id = args.profileid
folder_id = args.folderid

# Function to connect the agent

def connect_agent():
    path = "/opt/mlx/agent.bin"
    try:
        subprocess.Popen(['nohup', path, '&'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    except Exception as e:
        print("Can't open agent")

connect_agent()

# MLX Signin function to retrieve the toke
def signin() -> str:

    signin_endpoint = f'{MLX_BASE}/user/signin'
    
    payload = {
        'email': username,
        'password': password
    }

    r = requests.post(url=signin_endpoint, json=payload)

    if(r.status_code !=200):
        print(f'\nError during login: {r.text}\n')
    else:
        response = r.json()['data']
        token = response['token']
        print("Got token. Token is: " + token)
        return token
    
# Start profile and instantiate remote webdriver functions
def start_profile() -> webdriver:

    try:
        
        start_profile_endpoint = f'{MLX_LAUNCHER}/profile/f/{folder_id}/p/{profile_id}/start?automation_type=selenium'
        r = requests.get(url=start_profile_endpoint, headers=HEADERS)
        response = r.json()

        if(response['status']['message']=="downloading of core started"):
            try:
                print("Browser core is still downloading. Will wait for 20 seconds and try again.")
                time.sleep(20)
                start_profile_endpoint = f'{MLX_LAUNCHER}/profile/f/{folder_id}/p/{profile_id}/start?automation_type=selenium'
                r = requests.get(url=start_profile_endpoint, headers=HEADERS)
                response = r.json()
                selenium_port = response.get('status').get('message')
                print("Selenium port is: " + selenium_port + "\n")
                driver = webdriver.Remote(command_executor=f'{LOCALHOST}:{selenium_port}', options=ChromiumOptions())
                return driver
            except:
                print("Something went wrong during after the retry.")

        elif(r.status_code !=200 and response['status']['message']!="downloading of core started"):
            print(f'\nError while starting profile: {r.text}\n')
        else:
            print(f'\nProfile {profile_id} started.\n')
            selenium_port = response.get('status').get('message')
            print("Selenium port is: " + selenium_port + "\n")
            driver = webdriver.Remote(command_executor=f'{LOCALHOST}:{selenium_port}', options=ChromiumOptions())
            return driver
    except:
        print("Something has happened during the launching and instantiating process. Check.")

def automation():

    driver = start_profile()

    list=[]

    def create_sheet(list):
        num_columns = 3
        columns=["Keyword", "Number of companies", "Company name"]
        data = [list[i:i+num_columns] for i in range(0, len(list), num_columns)]
        df = pd.DataFrame(data, columns=columns)
        print("DataFrame:")
        print(df)
        df.to_excel('list-output.xlsx', index=False)
    

    def check_div_presence(): # This is done so it does not break the code if div is not present
        try:
            div_elements = driver.find_element(By.ID, "tads")
            return True
        except NoSuchElementException as e:
            print(Colors.RED + "TADS div is not present." + Colors.RESET)
            return False

    for keyword in keywords:    
        try:
            print(f"Looking for the keyword" + Colors.ORANGE + f" '{keyword}' " + Colors.RESET + "now. Please wait a few seconds...\n")
            driver.get('https://www.google.com/')
            search_bar = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "APjFqb")))
            search_bar.click()
            time.sleep(1)
            search_bar.send_keys(keyword)
            time.sleep(1)
            search_bar.send_keys(Keys.RETURN)
            time.sleep(10)
            if check_div_presence():
                base_xpath = "/html/body/div[5]/div/div[10]/div/div[1]/div[2]/div"
                all_divs = driver.find_elements(By.XPATH, f"{base_xpath}/*/div/div/div/div[1]/a/div[2]/span[1]/span[2]/span[1]/div/span")
                print(Colors.GREEN + f"Number of companies found for keyword " + Colors.RESET + Colors.ORANGE + f"'{keyword}':" + Colors.RESET + f" {len(all_divs)}\n")
                for i, div_element in enumerate(all_divs, start=1):
                    print(Colors.MAGENTA + f"Company {i}: {div_element.text}\n" + Colors.RESET)
                    list.append(keyword)
                    list.append(len(all_divs))
                    list.append(str(div_element.text))
            else:
                print(Colors.RED + "No paid search found for this keyword.\n" + Colors.RESET)

        except Exception as e:
            print(f"Something went wrong during the automation process: {e}")
    create_sheet(list)

# connect_agent()
token = signin()
HEADERS.update({"Authorization": f'Bearer {token}'})
automation()

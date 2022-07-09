import requests
import json
from bs4 import BeautifulSoup as bs
import re
import time
from datetime import datetime
import pandas as pd
import os.path

#nb: edit this path to suit your system.
#path_to_file = "/home/ubuntu/f_projs/"
output_file = "namecheap_updates.txt"
url_update_base = "https://dynamicdns.park-your-domain.com/update?"
no_change_sleep=30
config_file = "config_urls.csv"
df_config = pd.read_csv(config_file)
#https://dynamicdns.park-your-domain.com/update?host=[host]&domain=[domain_name]&password=[ddns_password]&ip=[your_ip]

#test if output file exists, if not - create.
if not os.path.exists(path_to_file+output_file):
    #print("outputfile does not exist, creating empty file.")
    with open(path_to_file+output_file, 'w') as fp:
        pass

def get():
    endpoint = 'https://ipinfo.io/json'
    response = requests.get(endpoint, verify = True)
    if response.status_code != 200:
        return 'Status:', response.status_code, 'Problem with the request. Exiting.'
        exit()
    data = response.json()
    return data['ip']
    #return "1.1.111.1" #used this for testing

#get my ip
#old_public_ip = get()
#use this to force update first time this is run.
old_public_ip = "0.0.0.0"
#print("old_public_ip:", old_public_ip)


def update_ip(url):
    #
    r = requests.get(url)
    #soup = bs(r.text, 'html.parser')
    soup = bs(r.text, 'xml')
    errs = soup.find_all('errcount')
    if len(errs)>0:
        error_count = soup.find_all('errcount')[0].get_text()
    else:
        error_count = 0
    done_tags = soup.find_all('Done')
    if len(done_tags)>0:
        done = soup.find_all('Done')[0].get_text()
    else:
        done = ""
    return done=="true" and error_count==0


while True:
    #get public ip
    new_public_ip = get()
    #print("new_public_ip:", new_public_ip)
    #if new_public_ip == old_public_ip: do nothing, sleep.
    if new_public_ip == old_public_ip:
        #print("no change, sleep. "+ str(datetime.now()))
        #print("no change in ip, sleeping...")
        time.sleep(no_change_sleep)
    else:
        #print("public ip changed, update namecheap records.")
        #new_public_ip != old_public_ip
        #
        #print("change in ip detected, updating namecheap.")
        url_update_base = "https://dynamicdns.park-your-domain.com/update?"
        df_update_results = pd.DataFrame()
        for index, row in df_config.iterrows():
            #print(index, row["domain_prefix"], row["domain"], row["password"])
            url = url_update_base \
                + "host="      + row["domain_prefix"] \
                + "&domain="   + row["domain"] \
                + "&password=" + row["password"] \
                + "&ip="       + new_public_ip
            #print(url)
            update_result = update_ip(url)
            row['update_result']=update_result
            row['update_time'] = str(datetime.now())
            row['old_public_ip']=old_public_ip
            row['new_public_ip']=new_public_ip
            #print("row",row)
            df_update_results = pd.concat([df_update_results, pd.DataFrame([row])], ignore_index=True)
        #
        #print("df_update_results\n", df_update_results)
        df_update_results.to_csv(path_to_file+output_file, mode='a', index=False, header=False)
        #
        old_public_ip = new_public_ip

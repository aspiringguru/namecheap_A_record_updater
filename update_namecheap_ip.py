import requests
import json
from bs4 import BeautifulSoup as bs
import re
import time
from datetime import datetime
import pandas as pd
import os.path
import ipinfo
from requests import get

path_to_file = "/home/m/f_projs/namecheap_ip_update/"  #nb: check this on installed site.
#path_to_file = os.getcwd()+"/"  #use this for local dev.
output_file = "namecheap_updates.txt"
output_file_no_change = "namecheap_updates_no_change.txt"
log_file = "error_log.txt"
url_update_base = "https://dynamicdns.park-your-domain.com/update?"
no_change_sleep=30
config_file = "config_urls.csv"
df_config = pd.read_csv(path_to_file+config_file)
ipinfo_token = "<get your own free token>"
#can make 50k calls/month on free level, approx once/minute.
handler = ipinfo.getHandler(ipinfo_token)
#https://dynamicdns.park-your-domain.com/update?host=[host]&domain=[domain_name]&password=[ddns_password]&ip=[your_ip]

#test if output file exists, if not - create.
if not os.path.exists(path_to_file+output_file):
    #print("outputfile does not exist, creating empty file.")
    with open(path_to_file+output_file, 'w') as fp:
        pass

def get():
    data = handler.getDetails().all
    if 'ip' not in data.keys() or type(data['ip']) != str:
        print("unable to retrieve ip from ipinfo.io api, try api.ipify.org.")
        public_ip = get('https://api.ipify.org').text
    else:
        print("public_ip retrieved from ipinfo.io")
        public_ip = data['ip']
    print("public_ip retrieved, public_ip:", public_ip)
    return public_ip
    #return "1.1.111.1" #used this for testing


#get my ip
#old_public_ip = get()
#use this to force update first time this is run.
old_public_ip = "0.0.0.0"
#new_public_ip= "1.1.1.1"
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
        print("update_namecheap_ip.py : no change, sleep. "+ str(datetime.now()))
        df_update_no_change = pd.DataFrame([new_public_ip, old_public_ip, str(datetime.now())] ).T
        df_update_no_change.columns = ["new_public_ip", "old_public_ip", "datetime"]
        df_update_no_change.to_csv(path_to_file+output_file_no_change, mode='a', index=False, header=False)
        #print("no change in ip, sleeping...")
        time.sleep(no_change_sleep)
    else:
        print("update_namecheap_ip.py public ip changed, update namecheap records.")
        #new_public_ip != old_public_ip
        #
        #print("change in ip detected, updating namecheap.")
        url_update_base = "https://dynamicdns.park-your-domain.com/update?"
        df_update_results = pd.DataFrame()
        for index, row in df_config.iterrows():
            #print(index, row["domain_prefix"], row["domain"], row["password"])
            #print("row:", row)
            #nb: error previously occurred if exceede free threshold usage of ipinfo.io
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

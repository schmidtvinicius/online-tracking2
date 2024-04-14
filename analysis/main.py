"""
This file should complete a bunch of analysis tasks on the HAR files and the crawl data.

1. Table with number of timeouts and failures in the accept and on the block crawlers.

2. Box plots with
    a. Page load time
    b. Number of requests
    c. Number of distinct third-party domains
    d. Number of distinct tracker domains
    e. Number of distinct third-party domains that set a cookie with SameSite=None

3. Get the min, the median, and the max from the metrics in 2.

4. Add a table of ten most prevalent third-party domains (based on the number of distinct
websites where the third party is present), indicating whether the domain is classified as
a tracker or not by Disconnect

5. Add a frequency table of HTTP methods (such as GET, POST, ..) for each crawl.

6. Analyze the Permissions-Policy headers encountered in the crawls and make a list of
websites that disable access to camera, geolocation or microphone for all parties
(including first and third). In total, you should make 6 separate website lists: 2 crawls x 3
permissions

7. Analyze the Referrer-Policy headers encountered in the crawl data, and make a list of
websites that use no-referrer or unsafe-url values (separately). In total, you should make 4
separate lists: 2 crawls x 2 Referrer-Policy value

8. Analyze the Accept-CH headers encountered in the crawl data, and make a list of 3
high-entropy client hints that are requested on most websites

9. For each crawl, identify the 3 most prevalent (by distinct websites) cross-domain HTTP
redirection (source, target) pairs. Cross-domain redirection means the source and target
of the redirection has different eTLD+1’s
"""

import os
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from har_analysis import get_har_metrics


def get_data(folder_name):
    print(folder_name)
    data = {}
    
    # get json 
    with open(f'{folder_name}/analysis.json', 'r') as f:
        analysis_data = json.load(f)
        data["failures"] = analysis_data["cookies_not_found"]
        data["timeouts"] = analysis_data["timeouts"]

    # get dicts from har files
    data["crawls"] = []
    for file_name in os.listdir(folder_name):
        if file_name.endswith('.har') and "investinholland.com_allow.har" != file_name:
            print(file_name)
            har = f'{folder_name}/{file_name}' 
            data['crawls'].append(get_har_metrics(har))

    return data


def get_accept_data():
    return get_data('crawl_data_allow')


def get_blocked_data():
    return get_data('crawl_data_block')


def get_num_timeouts_failures(accept_data, reject_data):
    # 1. Table with number of timeouts and failures in the accept and on the block crawlers.

    accept_timeouts = accept_data["timeouts"]
    accept_failures = accept_data["failures"]
    block_timeouts = reject_data["timeouts"]
    block_failures = reject_data["failures"]
    
    df = pd.DataFrame({
        'Crawler': ['Accept', 'Block'],
        'Timeouts': [accept_timeouts, block_timeouts],
        'Failures': [accept_failures, block_failures]
    })

    print(df)
    

def make_num_box_plots(accept_data, blocked_data):
    # 2. Box plots with
    #     a. Page load time
    #     b. Number of requests
    #     c. Number of distinct third-party domains
    #     d. Number of distinct tracker domains
    #     e. Number of distinct third-party domains that set a cookie with SameSite=None

    data = {}

    for crawl_data, name in zip([accept_data, blocked_data],["accept", "blocked"]):
        page_load_times = []
        num_requests = []
        num_third_party_domains = []
        num_tracker_domains = []
        num_third_party_domains_same_site_none = []

        for crawl in crawl_data["crawls"]:
            page_load_times.append(crawl['load_time'])
            num_requests.append(crawl['num_reqs'])
            num_third_party_domains.append(len(crawl['third_party_domains']))
            num_tracker_domains.append(len(crawl['tracker_cookie_domains']))
            num_third_party_domains_same_site_none.append(
                len([domain for domain in crawl['third_party_domains'] if domain in crawl['tracker_cookie_domains']])
            )

        data[name] = {
            'page_load_times': page_load_times,
            'num_requests': num_requests,
            'num_third_party_domains': num_third_party_domains,
            'num_tracker_domains': num_tracker_domains,
            'num_third_party_domains_same_site_none': num_third_party_domains_same_site_none
        }  
            
    fig, axs = plt.subplots(5)
    fig.suptitle('Box plots of page load time, number of requests, number of distinct third-party domains, number of distinct tracker domains, and number of distinct third-party domains that set a cookie with SameSite=None')
    axs[0].boxplot([data['accept']['page_load_times'], data['blocked']['page_load_times']])
    axs[0].set_title('Page load times')
    axs[1].boxplot([data['accept']['num_requests'], data['blocked']['num_requests']])
    axs[1].set_title('Number of requests')
    axs[2].boxplot([data['accept']['num_third_party_domains'], data['blocked']['num_third_party_domains']])
    axs[2].set_title('Number of distinct third-party domains')
    axs[3].boxplot([data['accept']['num_tracker_domains'], data['blocked']['num_tracker_domains']])
    axs[3].set_title('Number of distinct tracker domains')
    axs[4].boxplot([data['accept']['num_third_party_domains_same_site_none'], data['blocked']['num_third_party_domains_same_site_none']])
    axs[4].set_title('Number of distinct third-party domains that set a cookie with SameSite=None')
    plt.savefig('box_plots.png')
    plt.close()

    return data


def get_stats_from_box_plots(data):
    for key in data:
        print(f"{key}:")
        for metric in data[key]:
            print(f"{metric}:")
            print(f"Min: {min(data[key][metric])}")
            print(f"Median: {pd.Series(data[key][metric]).median()}")
            print(f"Max: {max(data[key][metric])}")
            print()


def get_top_ten_third_party_domains(accept_data, blocked_data):
    # 4. Add a table of ten most prevalent third-party domains (based on the number of distinct
    # websites where the third party is present), indicating whether the domain is classified as
    # a tracker or not by Disconnect

    accept_third_party_domains = {}
    for crawl in accept_data["crawls"]:
        for domain in crawl['third_party_domains']:
            if domain not in accept_third_party_domains:
                accept_third_party_domains[domain] = 0
            accept_third_party_domains[domain] += 1

    blocked_third_party_domains = {}
    for crawl in blocked_data["crawls"]:
        for domain in crawl['third_party_domains']:
            if domain not in blocked_third_party_domains:
                blocked_third_party_domains[domain] = 0
            blocked_third_party_domains[domain] += 1

    tracker = []
    for crawl in accept_data["crawls"]:
        for domain in crawl['tracker_cookie_domains']:
            if domain in accept_third_party_domains.keys():
                tracker.append(domain)

    for crawl in blocked_data["crawls"]:
        for domain in crawl['tracker_cookie_domains']:
            if domain in blocked_third_party_domains.keys():
                tracker.append(domain)
    
    domains = np.unique(list(accept_third_party_domains.keys()) + list(blocked_third_party_domains.keys()))
    df = pd.DataFrame({
        'Domain': domains,
        'Accept': [0] * len(domains),
        "Blocked": [0] * len(domains),
        'isTracker?': [0] * len(domains)
    })

    for domain in domains:
        if domain in accept_third_party_domains:
            df.loc[df['Domain'] == domain, 'Accept'] = accept_third_party_domains[domain]
        if domain in blocked_third_party_domains:
            df.loc[df['Domain'] == domain, 'Blocked'] = blocked_third_party_domains[domain]
        if domain in tracker:
            df.loc[df['Domain'] == domain, 'isTracker?'] = 1

    df['sum'] = df['Accept'] + df['Blocked']
    df = df.sort_values('sum', ascending=False)
    df = df.drop('sum', axis=1)
    print(df.head(10))

if __name__ == '__main__':
    # Load the data
    print("Loading data...")
    accept_data = get_accept_data()
    blocked_data = get_blocked_data()

    # 1. Table with number of timeouts and failures in the accept and on the block crawlers.
    print("Exercise 1...")
    get_num_timeouts_failures(accept_data, blocked_data)

    # 2. Box plots
    print("Exercise 2...")
    data = make_num_box_plots(accept_data, blocked_data)

    # 3. Get the min, the median, and the max from the metrics in 2.
    print("Exercise 3...")
    get_stats_from_box_plots(data)
        
    # 4. Add a table of ten most prevalent third-party domains (based on the number of distinct
    # websites where the third party is present), indicating whether the domain is classified as
    # a tracker or not by Disconnect
    # print("Exercise 4...")
    get_top_ten_third_party_domains(accept_data, blocked_data)


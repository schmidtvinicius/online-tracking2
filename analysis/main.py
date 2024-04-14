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

import matplotlib.pyplot as plt
import pandas as pd

def get_accept_data():
    pass


def get_blocked_data():
    pass


def get_num_timeouts_failures(accept_data, reject_data):
    # 1. Table with number of timeouts and failures in the accept and on the block crawlers.
    accept_timeouts = 0
    accept_failures = 0
    block_timeouts = 0
    block_failures = 0

    for crawl in accept_data:
        if crawl['timeouts'] > 0:
            accept_timeouts += 1
        if crawl['failures'] > 0:
            accept_failures += 1

    for crawl in reject_data:
        if crawl['timeouts'] > 0:
            block_timeouts += 1
        if crawl['failures'] > 0:
            block_failures += 1
    
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

    for crawl_data in [accept_data, blocked_data]:
        page_load_times = []
        num_requests = []
        num_third_party_domains = []
        num_tracker_domains = []
        num_third_party_domains_same_site_none = []

        for crawl in crawl_data:
            page_load_times.append(crawl['load_time'])
            num_requests.append(crawl['num_reqs'])
            num_third_party_domains.append(len(crawl['third_party_domains']))
            num_tracker_domains.append(len(crawl['tracker_cookie_domains']))
            num_third_party_domains_same_site_none.append(
                len([domain for domain in crawl['third_party_domains'] if domain in crawl['tracker_cookie_domains']]))

        data[crawl_data.name] = {
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
    # TODO


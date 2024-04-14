import json
import tldextract
from typing import List, Dict, Any
from urllib.parse import urlparse
from datetime import datetime


def load_har_file(file_name: str) -> Dict[str, Any]:
    """
    Load the HAR file and return a dictionary with the content
    :param file_name: Name of the HAR file
    :return: Dictionary with the content of the HAR file
    """
    with open(f'{file_name}', 'r') as f:
        return json.load(f)
    

def save_json_file(file_name: str, data: Dict[str, Any]) -> None:
    """
    Save the dictionary in a JSON file
    :param file_name: Name of the file
    :param data: Dictionary with the content
    """
    with open(f'{file_name}', 'w') as f:
        json.dump(data, f, indent=4)


def open_json_file(file_name: str) -> Dict[str, Any]:
    """
    Open the JSON file and return a dictionary with the content
    :param file_name: Name of the JSON file
    :return: Dictionary with the content of the JSON file
    """
    with open(f'{file_name}', 'r') as f:
        return json.load(f)


def get_third_party_domains(har: Dict[str, Any]) -> List[str]:
    """
    Get the third-party domains from the HAR file
    :param har: Dictionary with the content of the HAR file
    :return: List of strings with the third-party domains
    """
    third_party_domains = set()

    website_domain = tldextract.extract(har['log']['pages'][0]['title']).registered_domain
    for entry in har['log']['entries']:
        url = entry['request']['url']
        parsed_url = tldextract.extract(url).registered_domain        
        if parsed_url != website_domain:
            third_party_domains.add(tldextract.extract(url).registered_domain)
    return list(third_party_domains)


def is_cross_site_tracking(cookie_string, min_lifespan_days=60):
    """
    Check if a cookie is using cross-site tracking
    :param cookie_string: String with the cookie attributes
    :param min_lifespan_days: Minimum lifespan of the cookie in days
    :return: Boolean indicating if the cookie is using cross-site tracking
    """

    # Parse the cookie string
    attrs = cookie_string.split(';')
    cookie = {}
    for attr in attrs:
        if '=' in attr:
            key, value = attr.split('=', 1)
            cookie[key.strip()] = value.strip()

    # Check if the cookie has SameSite and (Max-Age or Expires)
    if 'SameSite' in cookie and ('Max-Age' in cookie or 'Expires' in cookie):
        same_site_value = cookie['SameSite']
        # Check if the cookie is using SameSite=None
        if same_site_value.lower() == 'none':
            if 'Max-Age' in cookie:
                max_age_seconds = int(cookie['Max-Age'])
            elif 'Expires' in cookie:
                expires_string = cookie['Expires']
                expires_datetime = datetime.strptime(expires_string, "%a, %d-%b-%Y %H:%M:%S GMT")
                max_age_seconds = (expires_datetime - datetime.utcnow()).total_seconds()

            if max_age_seconds >= min_lifespan_days * 24 * 60 * 60:
                return True
            
    return False


def get_tracker_cookie_domains(har: Dict[str, Any]) -> List[str]:
    """
    Get the tracker cookie domains from the HAR file
    :param har: Dictionary with the content of the HAR file
    :return: List of strings with the tracker cookie domains
    """
    tracker_cookie_domains = set()

    # Iterate through entries in the HAR file
    for entry in har.get("log", {}).get("entries", []):
        response = entry.get("response", {})
        headers = response.get("headers", [])

        # Check each header for Set-Cookie
        for header in headers:
            if header.get("name", "").lower() == "set-cookie":
                cookie_attributes = header.get("value", "")
                if is_cross_site_tracking(cookie_attributes):
                    attrs = cookie_attributes.split(';')
                    cookie = {}
                    for attr in attrs:
                        if '=' in attr:
                            key, value = attr.split('=', 1)
                            cookie[key.strip()] = value.strip()
                    domain = cookie["Domain"]
                    tracker_cookie_domains.add(domain)

    return list(tracker_cookie_domains)


def get_entity_name(domain: str, mapper: Dict[str, Any]) -> str:
    """
    Get the entity name from the domain
    :param domain: Domain name
    :return: Entity name
    """
    if domain in mapper:
        return mapper[domain]["entityName"]
    else:
        return 'unknown'


def get_third_party_entities(har: Dict[str, Any]) -> List[str]:
    """
    Get the third-party entities from the HAR file
    :param har: Dictionary with the content of the HAR file
    :return: List of strings with the third-party entities
    """
    domain_map = open_json_file('domain_map.json')

    third_party_entities = set()
    for entry in har['log']['entries']:
        url = entry['request']['url']
        parsed_url = urlparse(url)
        # Check if the request is from a third-party (not the same eTLD+1 as the website)
        if parsed_url.netloc != har['log']['pages'][0]['title']:
            domain = tldextract.extract(url).registered_domain
            third_party_entities.add(get_entity_name(domain, domain_map))
    return list(third_party_entities)


def analyze_har(har: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze the HAR file and return a dictionary with the results
    :param har: Dictionary with the content of the HAR file
    :return: Dictionary with the results
    """
    num_reqs = len(har['log']['entries'])

    # num_requests_w_cookies: Integer; number of requests with a non-empty Cookie header
    num_requests_w_cookies = 0
    # num_responses_w_cookies: Integer; number of responses with a non-empty Set-Cookie header
    num_responses_w_cookies = 0

    domain_map = open_json_file('domain_map.json')
    
    requests_list = []
    for entry in har['log']['entries']:
        url = entry['request']['url']
        parsed_url = urlparse(url)
        url_first_128_char = url[:128]
        url_domain = parsed_url.netloc
        
        is_third_party = parsed_url.netloc != har['log']['pages'][0]['title']
        
        response = entry['response']
        headers = response['headers']
        
        set_http_cookies = False
        for header in headers:
            if header['name'] == 'set-cookie':
                set_http_cookies = True
        
        if set_http_cookies:
            num_responses_w_cookies += 1
        
        request = {
            'url_first_128_char': url_first_128_char,
            'url_domain': url_domain,
            'is_third_party': is_third_party,
            'set_http_cookies': set_http_cookies,
            'entity_name': get_entity_name(url_domain, domain_map)
        }
        requests_list.append(request)
        
        if 'cookies' in entry['request']:
            if entry['request']['cookies'] != []:
                num_requests_w_cookies += 1
    
    return {
        'load_time': har['log']['pages'][0]['pageTimings']['onLoad'],
        'num_reqs': num_reqs,
        'num_requests_w_cookies': num_requests_w_cookies,
        'num_responses_w_cookies': num_responses_w_cookies,
        'third_party_domains': get_third_party_domains(har),
        'tracker_cookie_domains': get_tracker_cookie_domains(har),
        'third_party_entities': get_third_party_entities(har),
        'requests': requests_list
    }


def get_har_metrics(in_har_name, out_json_name) -> None:
    results = {}

    har = load_har_file(in_har_name)
    results = analyze_har(har)
    save_json_file(out_json_name, results)

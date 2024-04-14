import json
import datetime
import email.utils
from tld import get_fld, get_tld, get_tld_names

# domain_name = 'zalando.nl'
# accept_har_file = domain_name+'_accept.har'
# reject_har_file = domain_name+'_reject.har'
# accept_json_file = domain_name+'_accept.json'
# reject_json_file = domain_name+'_reject.json'

def read_json_file(filepath: str) -> list[dict]:
    with open(filepath, 'r') as json_file:
        return json.load(json_file)

# For the HAR files, we are only interested in the `entries` array, which is what contains all request/response pairs.
# From here every reference to an entry refers to a request/response pair 
# accept_list = read_json_file(accept_har_file)['log']['entries']
domain_map = read_json_file('analysis/domain_map.json')

def entry_has_header(entry: dict, entry_component: str, header_name: str) -> bool:
    """
    Checks whether a request or response contains a specified header
    """
    valid_entry_components = ('request', 'response')
    if entry_component not in valid_entry_components:
        raise RuntimeError(f'attr \'entry_component\' must be one of {valid_entry_components}')
    
    for header in entry[entry_component]['headers']:
        if header.get('name') == header_name:
            return True
    return False


def is_third_party(entry: dict, first_party_domain: str) -> bool:
    return first_party_domain != get_fld(entry['request'].get('url'))


def get_cookie_attrs_as_dict(cookie: str) -> dict:
    """
    Converts a cookie string, e.g. receive-cookie-deprecation=1; Domain=doubleclick.net; Secure; HttpOnly; Path=/; SameSite=None; Partitioned; Max-Age=15552000
    to a dictionary where the key is the name of the cookie attribute and the value is the value of the attribute. If the attribute
    is its own value, e.g. Secure, then key and value are the same.
    """
    return {x[0]: x[1] if(len(x) == 2) else x[0] for x in map(lambda x: x.strip().lower().split('='), cookie.split(';'))}


def is_cookie_age_greater_than(cookie: str, min_age_in_days: int) -> bool:
    cookie_attrs = get_cookie_attrs_as_dict(cookie)
    max_age = cookie_attrs.get('max-age')
    
    if max_age != None and datetime.timedelta(seconds=int(max_age)).days >= min_age_in_days:
        return True
    
    # In order for this script to keep working in the future, we'll compare the expiration date of the cookie 
    # to the date when the data was collected, instead of comparing it with `datetime.datetime.today()
    date_of_collection = datetime.datetime(year=2024, month=2, day=28,tzinfo=datetime.timezone.utc)
    expires = cookie_attrs.get('expires')
    
    if expires != None and (email.utils.parsedate_to_datetime(expires) - date_of_collection).days >= min_age_in_days:
        return True
    
    return False
    

def has_tracking_cookies(entry: dict):
    for header in entry['response']['headers']:
        if header.get('name') == 'set-cookie' and 'samesite=none' in header.get('value').lower() and is_cookie_age_greater_than(header.get('value'), 60):
            return True
    return False


def map_entry_to_fld(entry: dict) -> str:
    return get_fld(entry['request'].get('url'))


def map_entry_to_tld(entry: dict) -> str:
    return get_tld(entry['request'].get('url'))


def map_entry_to_entity_name(entry: dict) -> str:
    entry_fld = map_entry_to_fld(entry)
    entity_dict = domain_map.get(entry_fld)

    # In my HAR file I found a URL that yielded an fld that did not match any entity name in `domain_map.json`, 
    # namely `d6tizftlrpuof.cloudfront.net`. When I used `get_tld()` instead of `get_fld()`
    # I got the correct match for the entity name. In principle, using the `get_tld()` method should not
    # be a problem, since that in the cases where it returns a tld, e.g. `co.uk`, it will not match with
    # any entry in the domain_map file
    if entity_dict == None:
        entity_dict = domain_map.get(map_entry_to_tld(entry))

    return entity_dict.get('entityName', 'unknown') if entity_dict != None else 'unknown'


def map_entry_to_summary_dict(entry: dict, first_party_domain: str) -> dict:
    summary_dict = {}
    url = entry['request'].get('url')
    summary_dict['url_first_128_char'] = url[:128] if len(url) > 128 else url
    summary_dict['url_domain'] = get_fld(url)
    summary_dict['is_third_party'] = is_third_party(entry, first_party_domain)
    summary_dict['set_http_cookies'] = entry_has_header(entry, 'response', 'set-cookie')
    summary_dict['entity_name'] = map_entry_to_entity_name(entry)

    return summary_dict


def produce_json(har_content: list[dict], first_party_domain: str) -> dict:
    result_dict = {}
    result_dict['num_reqs'] = len(har_content)
    result_dict['num_requests_w_cookies'] = len(list(filter(lambda entry: entry_has_header(entry, 'request', 'cookie'), har_content)))
    result_dict['num_responses_w_cookies'] = len(list(filter(lambda entry: entry_has_header(entry, 'response', 'set-cookie'), har_content)))
    result_dict['third_party_domains'] = list(set(map(map_entry_to_fld, filter(lambda entry: is_third_party(entry, first_party_domain), har_content))))
    result_dict['tracker_cookie_domains'] = list(set(map(map_entry_to_fld, filter(has_tracking_cookies, har_content))))
    result_dict['third_party_entities'] = list(set(map(map_entry_to_entity_name, har_content)))
    result_dict['requests'] = list(map(lambda entry: map_entry_to_summary_dict(entry, first_party_domain), har_content))
    return result_dict


def write_json_file(path: str, content: dict) -> None:
    with open(path, 'w') as json_file:
        json.dump(content, json_file, indent=4)
    

def get_har_metrics(har_file_name: str) -> dict:
    domain_name = har_file_name.split('_')[0]
    har_contents = read_json_file(har_file_name)['log']['entries']
    result_dict = produce_json(har_contents, domain_name)
    result_dict['load_time'] = read_json_file(har_file_name)['log']['pages'][0]['pageTimings']['onLoad']
    return  result_dict # Domain name é o nome do site

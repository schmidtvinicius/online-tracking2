'''
a frequency table of HTTP methods (such as GET, POST, ..) for each crawl
'''

from har_analysis import load_har_file

def get_methods(in_har_name) -> dict:
    results = {}
    har = load_har_file(in_har_name)

    methods = {}
    for entry in har['log']['entries']:
        method = entry['request']['method']
        if method not in methods:
            methods[method] = 1
        else:
            methods[method] += 1

    results['methods'] = methods
    return results


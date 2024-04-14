import os, re, sys
import numpy as np
from playwright.sync_api import sync_playwright, Playwright, Page, TimeoutError as PlaywrightTimeoutError, Request, Route
from time import sleep
from tld import get_fld
import json


def main(playwright: Playwright, options: dict) -> None:
    suffix = '_block' if options['block_trackers'] else '_allow'
    crawl_data_dir = 'crawl_data'+suffix

    chromium = playwright.chromium # or "firefox" or "webkit".
    browser = chromium.launch(headless=False)

    accept_phrases = read_file('accept_words.txt')

    # code for analysis
    cookies_not_found = 0
    timeouts = 0

    for url in options['urls']:
        print(f'Processing {url}')
        fld = get_fld(url)
        file_prefix = fld+suffix

        context = browser.new_context(
            record_har_path=os.path.join(crawl_data_dir,file_prefix+'.har'),
            record_video_dir=crawl_data_dir
        )
        page = context.new_page()

        if options['block_trackers']:
            page.route('**', lambda route, request: block_tracking_domains(route, request, get_blocked_trackers()))

        # set timeout to load the page to 30 seconds
        page.set_default_timeout(30000)
        try:
            page.goto(url)
        except PlaywrightTimeoutError:
            print(f'Timeout error: {url}')
            timeouts += 1
            page.close()
            context.close()
            continue
        
        sleep(10)
        # screenshot before accepting cookies
        page.screenshot(path=os.path.join(crawl_data_dir,file_prefix+'_pre_consent.png'))
        
        # Accept cookies
        cookie_found = False
        for phrase in accept_phrases:
            try:
                page.click(f"button:text('{phrase}')", timeout=200)
                cookie_found = True
                break
            except:
                try:
                    page.click(f"a:text('{phrase}')", timeout=200)
                    cookie_found = True
                    break
                except:
                    continue
        if not cookie_found:
            cookies_not_found += 1   
        print(f"cookie consent clicked: {cookie_found}")
        sleep(3)
        # reload fonts
        # page.reload()
        sleep(3)
        # screenshot after accepting cookies
        page.screenshot(path=os.path.join(crawl_data_dir,file_prefix+'_post_consent.png'))
        scroll_in_multiple_steps(page)
        sleep(3)
        page.close()
        # Playwright does not allow you to specify the name of the video, so we have to manually rename it
        rename_video(page.video.path(), file_prefix+'.webm')
        context.close()
        
    browser.close()

    with open(os.path.join(crawl_data_dir,'analysis.json'), 'w') as f:
        f.write(f'{{"cookies_not_found": {cookies_not_found}, "timeouts": {timeouts}}}')

def get_blocked_trackers():
    # Read the JSON file
    data = None
    with open('tracker_domains.json', 'r') as f:
        data = json.load(f)
    # Create a list of blocked trackers
    blocked_trackers = []

    for category in data["categories"]:
        for company in data["categories"][category]:
            domains = list(list(company.values())[0].values())
            blocked_trackers += domains[0]
    blocked_trackers = set(blocked_trackers)

    return blocked_trackers


def block_tracking_domains(route: Route, request: Request, blocked_urls: list[str]) -> None:
    route.abort() if get_fld(request.url) in blocked_urls else route.continue_()


def scroll_in_multiple_steps(page: Page):
    at_bottom = False
    current_y_position = page.evaluate('window.scrollY')
    previous_y_position = current_y_position
    while not at_bottom:
        # Using a trackpad, a single swipe scrolls about 1200 pixels
        scroll_by = 1200 + np.random.randint(low=-100, high=100)
        page.evaluate(f'window.scrollBy(0,{scroll_by})')
        sleep(0.5+np.random.rand())
        current_y_position = page.evaluate('window.scrollY')
        at_bottom = current_y_position == previous_y_position
        previous_y_position = current_y_position


def rename_video(path_to_video: str, new_name: str) -> None:
    new_path = path_to_video.split('/')[:-1]
    new_path.append(new_name)
    new_path = '/'.join(new_path)
    try:
        os.rename(path_to_video, new_path)
    except OSError as e:
        print(f'Failed to rename video with exception: {e.strerror}')


def read_file(file_path: str) -> list[str]:
    with open(file_path, 'r') as f:
        return [line.strip() for line in f.readlines()]


def parse_command_line_args(args: list[str]) -> dict:
    if len(args) < 3 or len(args) > 4: raise AssertionError('too many or too little arguments given')
    if '-u' in args and '-l' in args: raise AssertionError('cannot provide -u and -l at the same time')
    if not '-u' in args and not '-l' in args: raise AssertionError('expected one of [-u <example.com> | -l <sites-list.txt>], but none were given')

    parsed_args = {}
    parsed_args['block_trackers'] = '--block-trackers' in sys.argv
    parsed_args['urls'] = [args[args.index('-u')+1]] if '-u' in args else read_file(args[args.index('-l')+1])
    return parsed_args

    
if __name__ == '__main__':
    command_line_args = parse_command_line_args(sys.argv)
    with sync_playwright() as playwright:
        main(playwright=playwright, options=command_line_args)

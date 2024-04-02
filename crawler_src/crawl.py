import os, sys
from playwright.sync_api import sync_playwright, Playwright
from time import sleep
from tld import get_fld

def main(playwright: Playwright, options) -> None:
    suffix = '_block' if options['block_trackers'] else '_allow'
    crawl_data_dir = 'crawl_data'+suffix

    chromium = playwright.chromium # or "firefox" or "webkit".
    browser = chromium.launch(headless=False)
    for url in options['urls']:
        fld = get_fld(url)
        file_prefix = fld+suffix
        page = browser.new_page(
            record_har_path=os.path.join(crawl_data_dir,file_prefix+'.har'),
            record_video_dir=os.path.join(crawl_data_dir))
        page.goto(url)
        sleep(10)
        page.screenshot(path=os.path.join(crawl_data_dir,file_prefix+'_pre_consent.png'))
        page.close()
        
    browser.close()


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

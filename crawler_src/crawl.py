import sys
from playwright.sync_api import sync_playwright, Playwright

def main(playwright: Playwright, block_trackers=False) -> None:
    crawl_data_dir = 'crawl_data_block' if block_trackers else 'crawl_data_allow'
    chromium = playwright.chromium # or "firefox" or "webkit".
    browser = chromium.launch(headless=False)
    page = browser.new_page()
    page.goto('https://playwright.dev/python/docs/api/class-playwright')
    page.screenshot(path=crawl_data_dir+'test')
    # other actions...
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
        main(playwright, block_trackers=command_line_args['block_trackers'])

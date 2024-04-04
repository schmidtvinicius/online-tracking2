import asyncio, os, sys
from playwright.sync_api import sync_playwright, Playwright, Mouse, TimeoutError as PlaywrightTimeoutError
from time import sleep
from tld import get_fld

async def main(playwright: Playwright, options: dict) -> None:
    suffix = '_block' if options['block_trackers'] else '_allow'
    crawl_data_dir = 'crawl_data'+suffix

    chromium = playwright.chromium # or "firefox" or "webkit".
    browser = chromium.launch(headless=False)
    accept_phrases = read_file('accept_words.txt')
    for url in options['urls']:
        fld = get_fld(url)
        file_prefix = fld+suffix
        context = browser.new_context(
            record_har_path=os.path.join(crawl_data_dir,file_prefix+'.har'),
            record_video_dir=crawl_data_dir
        )
        page = context.new_page()
        page.goto(url)
        sleep(10)
        page.screenshot(path=os.path.join(crawl_data_dir,file_prefix+'_pre_consent.png'))
        for phrase in accept_phrases:
            try:
                page.locator(selector="button", has_text=phrase).click(timeout=150)
                break
            except PlaywrightTimeoutError:
                continue
        sleep(3)
        await scroll_in_multiple_steps(page.mouse)
        page.screenshot(path=os.path.join(crawl_data_dir,file_prefix+'_post_consent.png'))
        page.close()
        # Playwright does not allow you to specify the name of the video, so we have to manually rename it
        rename_video(page.video.path(), file_prefix+'.webm')
        context.close()
        
    browser.close()


async def scroll_in_multiple_steps(mouse: Mouse):
    await mouse.wheel(delta_x=0,delta_y=300)


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
        asyncio.run(main(playwright=playwright, options=command_line_args))

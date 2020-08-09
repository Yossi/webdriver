import os
import re
import logging
import platform
from zipfile import ZipFile
from io import BytesIO
from time import sleep
import requests
from selenium import webdriver
from selenium.common.exceptions import SessionNotCreatedException

def get_chrome_version():
    version_commands = {
        'Linux': 'google-chrome --version',
        'Darwin': r'/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version',
        'Windows': r'reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version'
    }

    version = re.search(r'\d+\.\d+\.\d+', os.popen(version_commands[platform.system()]).read())
    if not version:
        raise ValueError('Could not find Chrome version')
    return version.group(0)

def make_executable(path):
    if platform.system() != 'Windows':
        mode = os.stat(path).st_mode
        mode |= (mode & 0o444) >> 2 # copy R bits to X
        os.chmod(path, mode)

def update_chromedriver(version=''):
    if not version:
        version = requests.get('https://chromedriver.storage.googleapis.com/LATEST_RELEASE').text.strip() # google claims this url is depricated but I wont fix this untill they break it
    arch = {'Linux': 'linux64', 'Darwin': 'mac64', 'Windows': 'win32'}[platform.system()] # these are the only options available
    logging.info('%s detected', arch)
    url = 'https://chromedriver.storage.googleapis.com/{}/chromedriver_{}.zip'.format(version, arch)
    logging.info(f'downloading chromedriver {version} ...')
    zip_file = ZipFile(BytesIO(requests.get(url).content))
    for name in zip_file.namelist():
        if name.startswith('chromedriver'):
            logging.info('unpacking...')
            with open(name, 'wb') as out:
                out.write(zip_file.read(name))
            logging.info('ready')
            break

def get_driver(headless=False):
    options = webdriver.ChromeOptions()
    options.add_argument('log-level=3')
    options.add_argument("user-data-dir=profile/")
    if headless:
        options.add_argument('headless')
        options.add_argument('disable-gpu')
        #options.add_argument('start-maximized')
        options.add_argument('enable-automation')
        options.add_argument('no-sandbox')
        options.add_argument('disable-infobars')
        options.add_argument('disable-dev-shm-usage')
        options.add_argument('disable-browser-side-navigation')

    # assume chrome is installed. anything else is out of scope
    # http://chromedriver.chromium.org/downloads/version-selection
    chrome_version = get_chrome_version() #1
    version_check_url = 'https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{}'.format(chrome_version) #2
    matching_CD_version = requests.get(version_check_url).text.strip() #3

    if not (os.path.isfile('chromedriver') or os.path.isfile('chromedriver.exe')): # bootstrap self
        logging.info('chromedriver not found')
        update_chromedriver(matching_CD_version) #4
        make_executable('./chromedriver')

    try:
        driver = webdriver.Chrome('./chromedriver', chrome_options=options) # assumes our version of chromedriver works with our version of chrome
        CD_version = driver.capabilities['chrome']['chromedriverVersion'].split()[0]
        if CD_version != matching_CD_version: #5
            driver.quit() # need to release the file lock
            logging.info('have chromedriver {}. attempting to update to {}'.format(CD_version, matching_CD_version))
            update_chromedriver(matching_CD_version) #4
            driver = webdriver.Chrome('./chromedriver', chrome_options=options) # reopen with fresh new chromedriver
    except SessionNotCreatedException:
        # there is a built-in assumption here that chromedriver version wont ever get ahead of chrome
        update_chromedriver() # so far out of date that just grabbing the newest is the way to go
        driver = webdriver.Chrome('./chromedriver', chrome_options=options)
    return driver



def test():
    try:
        driver = None
        logging.info('get driver...')
        driver = get_driver(headless=True)
        driver.implicitly_wait(5)
        #driver.set_window_size(1024, 768)
        logging.info('waiting on get()')
        driver.get('https://www.noip.com/login')
        sleep(1)

    finally:
        if driver:
            logging.info('cleanup')
            driver.quit()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(message)s',
                        datefmt='%H:%M:%S')
    test()

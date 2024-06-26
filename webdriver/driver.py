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

import tarfile
import tempfile
from webdriver_manager.firefox import GeckoDriverManager


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

def get_firefox_version():
    ''' only been tested on linux '''
    version_commands = {
        'Linux': 'firefox --version',
        #'Darwin': r'/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version',
        'Windows': r'reg query "HKLM\SOFTWARE\Mozilla\Mozilla Firefox" /v CurrentVersion'
    }

    version = re.search(r'\d+\.\d+\.\d+', os.popen(version_commands[platform.system()]).read())
    if not version:
        raise ValueError('Could not find Firefox version')
    return version.group(0)

def make_executable(path):
    if platform.system() != 'Windows':
        mode = os.stat(path).st_mode
        mode |= (mode & 0o444) >> 2 # copy R bits to X
        os.chmod(path, mode)

def update_chromedriver(version=''):
    if not version:
        version = requests.get('https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_STABLE').text.strip()
    arch = {'Linux': 'linux64', 'Darwin': 'mac64', 'Windows': 'win32'}[platform.system()] # these are the only options available
    logging.info('%s detected', arch)
    url = 'https://storage.googleapis.com/chrome-for-testing-public/{}/linux64/chromedriver-{}.zip'.format(version, arch)
    logging.info(f'downloading chromedriver {version} ...')
    zip_file = ZipFile(BytesIO(requests.get(url).content))
    for name in zip_file.namelist():
        if name.startswith(f'chromedriver-{arch}/chromedriver'):
            logging.info('unpacking...')
            with open(os.path.basename(name), 'wb') as out:
                out.write(zip_file.read(name))
            logging.info('ready')
            break

def update_geckodriver(version=''):
    if not version:
        webpage = requests.get('https://firefox-source-docs.mozilla.org/_sources/testing/geckodriver/Support.md.txt').text
        index = webpage.index('<td')
        version = webpage[index+4:index+10]
    arch = {'Linux': 'linux64.tar.gz', 'Darwin': 'macos.tar.gz', 'Windows': 'win64.zip'}[platform.system()]
    logging.info('%s detected', arch)
    url = 'https://github.com/mozilla/geckodriver/releases/download/v{}/geckodriver-v{}-{}'.format(version, version, arch)
    logging.info(f'downloading geckodriver {version} ...')

    if url.endswith('tar.gz'):
        with tempfile.NamedTemporaryFile() as t:
            t.write(requests.get(url).content)
            tar = tarfile.open(t.name, 'r:*')
            tar.extract('geckodriver')

    if url.endswith('zip'):
        zip_file = ZipFile(BytesIO(requests.get(url).content))
        for name in zip_file.namelist():
            if name.startswith('geckodriver'):
                logging.info('unpacking...')
                with open(name, 'wb') as out:
                    out.write(zip_file.read(name))
                logging.info('ready')
                break

def get_driver(headless=False):
    ''' function here for backward compatibility '''
    return get_chrome_driver(headless)

def get_chrome_driver(headless=False):
    options = webdriver.ChromeOptions()
    options.add_argument('log-level=3')
    options.add_argument('user-data-dir=profile/')
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
    version_check_url = 'https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_{}'.format(chrome_version) #2
    matching_CD_version = requests.get(version_check_url).text.strip() #3

    if not (os.path.isfile('chromedriver') or os.path.isfile('chromedriver.exe')): # bootstrap self
        logging.info('chromedriver not found')
        update_chromedriver(matching_CD_version) #4
        make_executable('./chromedriver')

    service = webdriver.ChromeService('./chromedriver')

    try:
        driver = webdriver.Chrome(service=service, options=options) # assumes our version of chromedriver works with our version of chrome
        CD_version = driver.capabilities['chrome']['chromedriverVersion'].split()[0]
        if CD_version != matching_CD_version: #5
            driver.quit() # need to release the file lock
            logging.info('have chromedriver {}. attempting to update to {}'.format(CD_version, matching_CD_version))
            update_chromedriver(matching_CD_version) #4
            driver = webdriver.Chrome(service=service, options=options) # reopen with fresh new chromedriver
    except SessionNotCreatedException:
        # there is a built-in assumption here that chromedriver version wont ever get ahead of chrome
        update_chromedriver() # so far out of date that just grabbing the newest is the way to go
        driver = webdriver.Chrome(service=service, options=options)
    return driver


def get_firefox_driver(headless=False):
    if not os.path.exists('geckoprofile/'):
        os.makedirs('geckoprofile/')
    options = webdriver.FirefoxOptions()
    options.add_argument('--profile')
    options.add_argument('geckoprofile/')
    if headless:
        options.add_argument('--headless')

    driver = webdriver.Firefox(service_args=["--marionette-port", "2828"], executable_path=GeckoDriverManager(log_level=0).install(), options=options)
    return driver



def test():
    try:
        driver = None
        logging.info('get driver...')
        driver = get_firefox_driver(headless=True)
        driver.implicitly_wait(5)
        #driver.set_window_size(1024, 768)
        logging.info('waiting on get()')
        driver.get('https://www.noip.com/login')
        sleep(1)
        logging.info('nothing crashed')

    finally:
        if driver:
            logging.info('cleanup')
            driver.quit()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(message)s',
                        datefmt='%H:%M:%S')
    get_driver().get('https://selenium.dev')
    
    
    
    # test()
    # print(GeckoDriverManager(log_level=0).install())




    # # assume Firefox is installed. anything else is out of scope
    # if not (os.path.isfile('geckodriver') or os.path.isfile('geckodriver.exe')): # bootstrap self
    #     logging.info('geckodriver not found')
    #     update_geckodriver()
    #     # make_executable('./geckodriver')

    # try:
    #     service = webdriver.firefox.service.Service('geckodriver', port=2828)
    #     driver = webdriver.Firefox(service=service, options=options) # assumes our version of geckodriver works with our version of firefox
    # except SessionNotCreatedException:
    #     # there is a built-in assumption here that geckodriver version wont ever get ahead of firefox
    #     update_geckodriver() # so far out of date that just grabbing the newest is the way to go
    #     driver = webdriver.Firefox('./geckodriver', options=options) #############################################################################################
    # return driver

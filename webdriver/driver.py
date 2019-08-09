import os
import logging
import platform
from zipfile import ZipFile
from io import BytesIO
from time import sleep
import requests
from selenium import webdriver
from selenium.common.exceptions import SessionNotCreatedException

def make_executable(path):
    if platform.system() != 'win32':
        mode = os.stat(path).st_mode
        mode |= (mode & 0o444) >> 2 # copy R bits to X
        os.chmod(path, mode)

def update_chromedriver(version=''):
    if not version:
        version = requests.get('https://chromedriver.storage.googleapis.com/LATEST_RELEASE').text.strip() # google claims this url is depricated but I wont fix this untill they break it
    arch = {'Linux': 'linux64', 'Darwin': 'mac64', 'Windows': 'win32'}[platform.system()] # these are the only options available
    logging.info('%s detected', arch)
    url = 'https://chromedriver.storage.googleapis.com/{}/chromedriver_{}.zip'.format(version, arch)
    logging.info('downloading...')
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

    # assume chrome is installed. anything else is out of scope
    # http://chromedriver.chromium.org/downloads/version-selection
    if not (os.path.isfile('chromedriver') or os.path.isfile('chromedriver.exe')): # bootstrap self
        logging.info('chromedriver not found')
        update_chromedriver() # just get newest, dont worry about automatically matching chrome yet
        make_executable('./chromedriver')

    try:
        driver = webdriver.Chrome('./chromedriver', chrome_options=options) # assumes our version of chromedriver works with our version of chrome
        chrome_version = driver.capabilities[({'version', 'browserVersion'} & driver.capabilities.keys()).pop()] #1
        CD_version = driver.capabilities['chrome']['chromedriverVersion'].split()[0]
        version_check_url = 'https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{}'.format(chrome_version.rpartition('.')[0]) #2
        matching_CD_version = requests.get(version_check_url).text.strip() #3
        if CD_version != matching_CD_version: #5
            driver.quit() # need to release the file lock
            logging.info('have chromedriver {}. attempting to update to {}'.format(CD_version, matching_CD_version))
            update_chromedriver(matching_CD_version) #4
            driver = webdriver.Chrome('./chromedriver', chrome_options=options) # reopen with fresh new chromedriver
    except SessionNotCreatedException:
        update_chromedriver() # so far out of date that just grabbing the newest is the way to go
        driver = webdriver.Chrome('./chromedriver', chrome_options=options)
    return driver



def test():
    try:
        driver = None
        logging.info('get driver...')
        driver = get_driver()
        driver.implicitly_wait(5)
        driver.set_window_size(1024, 768)
        driver.get('https://www.github.com')
        sleep(2)

    finally:
        if driver:
            logging.info('cleanup')
            driver.quit()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(message)s',
                        datefmt='%H:%M:%S')
    test()

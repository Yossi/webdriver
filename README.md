# Webdriver Package

Gets you a webdriver while keeping chromedriver up to date keeping up with chrome itself as it updates.

Install with `pip install git+https://github.com/Yossi/webdriver#webdriver`

Import in your module:
```python
from webdriver import get_driver
```
Use as desired:
```python
try:
    driver = get_driver(HEADLESS)

    driver.implicitly_wait(5) # see selenium docs for more info on what you can do here
    driver.set_window_size(1024, 768)
    driver.get('https://www.github.com')

finally:
    if driver:
        driver.quit()
```
You dont need to have chromedriver, this will get it automatically. You *do* need to have chrome installed.  
Here's how to get Chrome on a headless ubuntu server:
```
curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add
sudo sh -c 'echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
sudo apt update
sudo apt -y install google-chrome-stable
```
This last command installs a crap ton of stuff. Like 100MB of stuff.

from https://gist.github.com/ziadoz/3e8ab7e944d02fe872c3454d17af31a5 more or less

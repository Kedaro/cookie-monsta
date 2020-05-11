# Cookie Monsta

## About

A cookie clicking robot for the game Cookie Clicker by Ortiel: https://orteil.dashnet.org/cookieclicker/  

Implemented in Python 3 using Selenium.  

Tested on Python 3.7, Chrome v 81.0.4044.122, Cookie Clicker v 2.022, \[Ubuntu 18.04 and macOS Catalina\]

### Consider becoming a supporter of the Cookie Clicker game! 
Patreon: https://www.patreon.com/dashnet \
Or buying some merch: redbubble.com/people/dashnet/shop


## How to use

1) Install Chrome driver: https://chromedriver.chromium.org/downloads
2) Install the python packages: `pip install -r requirements.txt`
3) Launch `python main.py -p <path_to_chrome_driver> -a <absolute_save_path> -s <purchase_strategy default=1>`

## About the command line arguments


1) --path_to_chrome_driver: REQUIRED Selenium needs a path to the Chrome driver.

2) --absolute_save_path: OPTIONAL (but recommended) A path to dir where the Chrome driver will save browser info.  Cookie Clicker has an auto-save function that will save the game state every 60 seconds.  By providing this path you will be able to resume games after closing the browser

3) --strategy: OPTIONAL The building purchase decisions of the robot are configurable.  Use the int value associated with the strategy for command line arg. There are currently two strategies that have been implemented:

1: Min (Cost/Cookies per Second)

    Every so often the robot scans all buildings and calculates the cost/CPS for each/ The building with the lowest ratio is chosen for the next purchase.

2: Frozen Cookies: Weighted Min (Cost/Cookies per Second)

    [Frozen Cookies](https://github.com/Icehawk78/FrozenCookies), another Cookie Clicker automator, experimentally devised a weighted strategy for [optimal building purchase](https://cookieclicker.fandom.com/wiki/Frozen_Cookies_(JavaScript_Add-on)):

    1.15 * (Cost/current CPS) + (Cost/delta CPS) 


## Known Issues
- Text wrapping can cause CPS parsing to fail if window size too small

## Future Work
- Automation of late game mechanics
    
    a) Sugar lumps
    
    b) Ascension

    c) Grandmapocalypse

    d) Research
from cookie_monsta import CookieClicker
import logging
import argparse

LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Cookie Monsta App')

    parser.add_argument('-p', '--path_to_chrome_driver',  required=True, type=str)
    parser.add_argument('-a', '--absolute_save_path', help="absolute save path, where game progress will be saved and loaded (recommended)", default="", type=str)
    parser.add_argument('-s', '--strategy', help="purchase strategy (int) see README for mapping", default=1, type=int)

    parser = parser.parse_args()

    cookie_clicker = CookieClicker(chrome_driver_path=parser.path_to_chrome_driver, purchase_strategy=parser.strategy, absolute_save_path=parser.absolute_save_path)
    try:
        cookie_clicker.run()  
    except Exception:
        logger.exception("Program failed with exception...", exc_info=True)
        cookie_clicker.clean_up()
    finally:
        pass
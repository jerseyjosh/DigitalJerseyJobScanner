import logging
import json
import importlib

from scanner import Scanner
from models import Config

logger = logging.getLogger(__name__)


def main():

    # load config
    try:
        config = Config.from_json("config.json")
    except ValueError as e:
        print(f"Error loading configuration: {e}")
        return
    
    # init logging
    level_string = config.log_level
    logging.basicConfig(level=getattr(logging, level_string))
    logging.getLogger('urllib3').setLevel(logging.ERROR)
    
    # get new_job_callback
    callback_name = config.new_job_callback
    if callback_name:
        try:
            module = importlib.import_module('callbacks')
            callback_func = getattr(module, callback_name)
        except (ImportError, AttributeError) as e:
            logger.error(f"Error loading new_job_callback: {callback_name} from callbacks.py: {e}")
            return
    else:
        callback_func = None
        logger.warning("No new_job callback specified")
    
    # run scanner
    scanner = Scanner(config, new_job_callback=callback_func)
    scanner.run()


if __name__ == "__main__":
    main()
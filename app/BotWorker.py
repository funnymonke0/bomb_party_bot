from celery import Celery
from dotenv import load_dotenv
from bomb_party_bot.BotManager import BotManager
import os
import logging
import threading
import signal

load_dotenv()
redis = os.getenv("RATELIMIT_STORAGE_URI", "redis://redis:6379/0")
worker_app = Celery(
    "runner",
    broker=redis,
    backend=redis
)
worker_app.conf.worker_max_tasks_per_child = 1 #wipe worker after every bot
@worker_app.task
def start_bot(dict_file : str, settings_file : str, invalid_file : str, room_code : str, username : str = '') -> None:
    bot_manager = None
    shutdown_event = threading.Event()
    def handle_revoke(signum, frame):
        logging.info(f"Received revoke signal: {signum}. Initiating cleanup...")
        if bot_manager:
            try:
                bot_manager.close()
            except Exception as close_error:
                logging.error(f"Error during bot close: {close_error}")
            logging.info("Bot cleanup complete.")
        raise Exception("Task revoked")
    signal.signal(signal.SIGTERM, handle_revoke)

    try:
        bot_manager = BotManager(
            dict_file = dict_file,
            room_code = room_code,
            username = username,
            settings_file = settings_file,
            invalid_file = invalid_file,
            secure = True,
            proxy_file="",
            shutdown_event=shutdown_event
        )

        bot_manager.persist_loop()
    except Exception as e:
        logging.error(f"Bot encountered an error: {e}")
        raise e
    finally:
        # This executes for unhandled or standard complete
        if bot_manager:
            logging.info(f"Task completed. Safely shutting down bot...")
            try:
                bot_manager.close()
            except Exception as close_error:
                logging.error(f"Error during bot close: {close_error}")
            logging.info("Bot cleanup complete.")
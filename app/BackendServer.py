import json
import logging
import os
import threading
import time

from flask import Flask, render_template, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import CSRFProtect
from flask_talisman import Talisman
from bomb_party_bot.BotManager import BotManager

logger = logging.getLogger(__name__)
config = "config"
proxies_file = os.path.join(config, 'proxies.config') ##adjust to autorecognize?
settings_file = os.path.join(config,'settings.json')
dictionaries_file = os.path.join(config,'dictionaries.config')
invalid_file = os.path.join(config,'invalid.config')





class BackendServer:
    def __init__(self, port = 5000, debug=False):
        self.app = Flask(__name__)
        Talisman(self.app)
        self.manager = None
        self.bot_thread = None
        self.lock = threading.RLock()
        self.port = port
        self.debug = debug

        self.csrf = CSRFProtect(self.app)
        self.limiter = Limiter(app=self.app, key_func=get_remote_address, default_limits=["60 per minute"])

        self.last_heartbeat = 0
        self.heartbeat_active = False

    def run(self):
        self._register_routes()
        self.app.run(debug=self.debug, port=self.port, use_reloader=False)

    def _register_routes(self):
        #rate limiter wrapping. would be a decorator if not inside class
        home_wrapped = self.limiter.limit("60 per minute")(self.home)
        settings_wrapped = self.limiter.limit("30 per minute")(self.get_settings)
        launch_wrapped = self.limiter.limit("3 per minute")(self.launch_bot)
        stop_wrapped = self.limiter.limit("10 per minute")(self.stop_bot)
        heartbeat_wrapped = self.limiter.limit("120 per minute")(self.heartbeat)
        # Maps endpoints directly to internal class methods.
        self.app.add_url_rule('/', 'home', home_wrapped)
        self.app.add_url_rule('/api/settings', 'get_settings', settings_wrapped, methods=['GET'])
        self.app.add_url_rule('/api/launch', 'launch_bot', launch_wrapped, methods=['POST'])
        self.app.add_url_rule('/api/stop', 'stop_bot', stop_wrapped, methods=['POST'])
        self.app.add_url_rule('/api/heartbeat', 'heartbeat', heartbeat_wrapped, methods=['POST'])


    def home(self):
        return render_template('index.html')


    def stop_bot(self):
        with self.lock:
            if self.manager:
                try:
                    self.manager.close()  # Gracefully stop the existing bot manager (maybe closed already)
                except Exception as e:
                    logger.warning(f"Error while closing bot manager: {e}")
            if self.bot_thread and self.bot_thread.is_alive():
                self.bot_thread.join(timeout=5)  # Wait for the thread to finish, with a timeout
            if self.bot_thread and self.bot_thread.is_alive():
                logger.warning("Error stopping bot: Thread did not terminate")
                return jsonify({"success": False, "error": "Error stopping bot. Bot did not terminate"}), 500

            self.manager = None
            self.bot_thread = None
            import gc
            gc.collect()
            time.sleep(0.1)  # Give a moment for resources to be released
            return jsonify({"success": True, "message": "Bot stopped."})


    def get_settings(self):
        settings = {}
        with open(settings_file, 'r') as f:
            settings = json.load(f)
        return jsonify(settings)


    def launch_bot(self):
        try:
            # 1. Grab incoming data from the HTML form
            data = request.json or {}
            with self.lock:
                if self.manager:
                    self.stop_bot()

                if self.bot_thread and self.bot_thread.is_alive():
                    return jsonify({"success": False, "error": "Error launching bot: Previous bot is still running"}), 500


                req_format = {
                    "username": str,
                    "roomcode": str,
                    "invalid": list,
                    "dictionaries": list,
                    "proxies": list,
                    "selectMode": str,
                    "regenIfNeeded": bool,
                    "sneakyRegen": bool,
                    "stockpile": bool,
                    "greedLong": bool,
                    "timeConstraint": bool,
                    "cyberbullying": bool,
                    "mistakes": bool,
                    "burstType": bool,
                    "spamType": bool,
                    "dynamicRate": bool,
                    "dynamicPauses": bool,
                    "dynamicMistakes": bool,
                    "minWait": int|float,
                    "maxWait": int|float,
                    "mistakePause": int|float,
                    "miniPause": int|float,
                    "minWpm": int|float,
                    "maxWpm": int|float,
                    "spamWpm": int|float,
                    "burstChance": int|float,
                    "minMistakeChance": int|float,
                    "maxMistakeChance": int|float,
                    "spamChance": int|float,
                    "jitterPercent": int|float
                }

                for key, expected_type in req_format.items():
                    if key not in data:
                        return jsonify({"success": False, "error": f"Missing key in data: {key}"}), 400
                    if not isinstance(data[key], expected_type):
                        return jsonify({"success": False,
                            "error": f"Incorrect type for key in data: {key}. Expected {expected_type.__name__}"}), 400

                settings = {}
                with open(settings_file, 'r') as f:
                    settings = json.load(f)


                # 2. Extract the necessary fields from the incoming data
                username = data["username"]
                room_code = data["roomcode"]
                invalid = data["invalid"]
                dictionaries = data["dictionaries"]
                proxies = data["proxies"]

                def get_val(setting:str):
                    return data.get(setting) if data.get(setting) is not None else settings.get(setting)
                settings = {
                    "selectMode": get_val("selectMode"),
                    "regenIfNeeded": get_val("regenIfNeeded"),
                    "sneakyRegen": get_val("sneakyRegen"),
                    "stockpile": get_val("stockpile"),
                    "greedLong": get_val("greedLong"),
                    "timeConstraint": get_val("timeConstraint"),
                    "cyberbullying": get_val("cyberbullying"),
                    "mistakes": get_val("mistakes"),
                    "burstType": get_val("burstType"),
                    "spamType": get_val("spamType"),
                    "dynamicRate": get_val("dynamicRate"),
                    "dynamicPauses": get_val("dynamicPauses"),
                    "dynamicMistakes": get_val("dynamicMistakes"),
                    "minWait": get_val("minWait"),
                    "maxWait": get_val("maxWait"),
                    "mistakePause": get_val("mistakePause"),
                    "miniPause": get_val("miniPause"),
                    "minWpm": get_val("minWpm"),
                    "maxWpm": get_val("maxWpm"),
                    "spamWpm": get_val("spamWpm"),
                    "burstChance": get_val("burstChance"),
                    "minMistakeChance": get_val("minMistakeChance"),
                    "maxMistakeChance": get_val("maxMistakeChance"),
                    "spamChance": get_val("spamChance"),
                    "jitterPercent": get_val("jitterPercent")
                }

                # 3. Overwrite the local config.json file
                with open(settings_file, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=4)
                logger.info(f"--> [SUCCESS] settings.json updated")

                if dictionaries and len(dictionaries) > 0:
                    with open(dictionaries_file, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(dictionaries)+'\n')
                    logger.info(f"--> [SUCCESS] dictionaries.config updated")
                else:
                    logger.warning(f"--> [WARNING] No dictionaries provided, skipping update and using defaults.")

                if invalid and len(invalid) > 0:
                    with open(invalid_file, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(invalid)+'\n')
                    logger.info(f"--> [SUCCESS] invalid.config updated")
                else:
                    logger.warning(f"--> [WARNING] No invalid words provided, skipping update and using defaults.")

                if proxies and len(proxies) > 0:
                    with open(proxies_file, 'w', encoding='utf-8') as f:
                            f.write('\n'.join(proxies)+'\n')
                    logger.info(f"--> [SUCCESS] proxies.config updated")
                else:
                    logger.warning(f"--> [WARNING] No proxies provided, skipping update and using defaults (None).")


                # 4. Launch the bot in a separate thread to avoid blocking the Flask server
                self.manager = BotManager(dict_file=dictionaries_file, room_code=room_code, proxy_file=proxies_file, username=username, settings_file=settings_file, invalid_file=invalid_file)
                self.bot_thread = threading.Thread(target=self.manager.persist_loop, daemon=True)
                self.bot_thread.start()

                self.last_heartbeat = time.time()
                if not self.heartbeat_active:
                    self.heartbeat_active = True
                    monitor_thread = threading.Thread(target=self._check_heartbeat, daemon=True)
                    monitor_thread.start()

                return jsonify({"success": True, "message": "Configuration saved! Bot running."})

        except Exception as e:
            logger.error(f"--> [ERROR] {e}")
            return jsonify({"success": False, "error":"internal error occurred"}), 500 #server side error

    def heartbeat(self):
        # Endpoint hit by the frontend every 2 seconds.
        self.last_heartbeat = time.time()
        return jsonify({"status": "alive"})

    def _check_heartbeat(self):
        while self.heartbeat_active:
            time.sleep(5)
            if time.time() - self.last_heartbeat > 10:  # If no heartbeat for 10 seconds
                self.stop_bot()
                self.heartbeat_active = False
                break



if __name__ == '__main__':
    # Runs web server locally on http://127.0.0.1:5000
    server = BackendServer(5000)
    server.run()

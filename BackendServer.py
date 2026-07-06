import time

from flask import Flask, render_template, request, jsonify
from BotManager import BotManager
import os
import json
import threading

config = "config"
proxies_file = os.path.join(config, 'proxies.config') ##adjust to autorecognize?
settings_file = os.path.join(config,'settings.json')
dictionaries_file = os.path.join(config,'dictionaries.config')
invalid_file = os.path.join(config,'invalid.config')

class BackendServer:
    def __init__(self, port = 5000, debug=False):
        self.app = Flask(__name__)
        self.manager = None
        self.bot_thread = None
        self.port = port
        self.debug = debug

        self.last_heartbeat = 0
        self.heartbeat_active = False

    def run(self):
        self._register_routes()
        self.app.run(debug=self.debug, port=self.port, use_reloader=False)

    def _register_routes(self):
        # Maps endpoints directly to internal class methods.
        self.app.add_url_rule('/', 'home', self.home)
        self.app.add_url_rule('/api/settings', 'get_settings', self.get_settings, methods=['GET'])
        self.app.add_url_rule('/api/launch', 'launch_bot', self.launch_bot, methods=['POST'])
        self.app.add_url_rule('/api/stop', 'stop_bot', self.stop_bot, methods=['POST'])
        self.app.add_url_rule('/api/heartbeat', 'heartbeat', self.heartbeat, methods=['POST'])

    def home(self):
        return render_template('index.html')


    def stop_bot(self):

        if self.manager:
            try:
                self.manager.close()  # Gracefully stop the existing bot manager (may be closed already)
            except Exception as e:
                print(f"--> [WARNING] Error while closing bot manager: {e}")
        if self.bot_thread and self.bot_thread.is_alive():
            self.bot_thread.join(timeout=5)  # Wait for the thread to finish, with a timeout
        if self.bot_thread and self.bot_thread.is_alive():
            return jsonify({"success": False, "error": "Error stopping bot: Thread did not terminate"}), 500

        self.manager = None
        self.bot_thread = None
        import gc
        gc.collect()
        time.sleep(0.1)  # Give a moment for resources to be released
        return jsonify({"success": True, "message": "Bot stopped."})
        return jsonify({"success": False, "error": "No bot is currently running."}), 400


    def get_settings(self):
        settings = {}
        with open(settings_file, 'r') as f:
            settings = json.load(f)
        return jsonify(settings)


    def launch_bot(self):
        try:
            # 1. Grab incoming data from the HTML form
            data = request.json or {}
            if self.manager:
                self.stop_bot()

            if self.bot_thread and self.bot_thread.is_alive():
                return jsonify({"success": False, "error": "Error launching bot: Previous bot thread is still running"}), 500

            settings = {}
            with open(settings_file, 'r') as f:
                settings = json.load(f)

            # 2. Extract the necessary fields from the incoming data
            username = data["username"]
            room_code = data["roomcode"]
            invalid = data["invalid"]
            dictionaries = data["dictionaries"]
            proxies = data["proxies"]

            def get_val(key):
                return data.get(key) if data.get(key) is not None else settings.get(key)
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
            print(f"--> [SUCCESS] settings.json updated")

            if dictionaries and len(dictionaries) > 0:
                with open(dictionaries_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(dictionaries)+'\n')
                print(f"--> [SUCCESS] dictionaries.config updated")
            else:
                print(f"--> [WARNING] No dictionaries provided, skipping update and using defaults.")

            if invalid and len(invalid) > 0:
                with open(invalid_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(invalid)+'\n')
                print(f"--> [SUCCESS] invalid.config updated")
            else:
                print(f"--> [WARNING] No invalid words provided, skipping update and using defaults.")

            if proxies and len(proxies) > 0:
                with open(proxies_file, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(proxies)+'\n')
                print(f"--> [SUCCESS] proxies.config updated")
            else:
                print(f"--> [WARNING] No proxies provided, skipping update and using defaults (None).")

            with open(invalid_file, 'r', encoding='utf-8') as f:
                print(f.read().splitlines())
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
            return jsonify({"success": False, "error": str(e)}), 500 #server side error

    def heartbeat(self):
        """Endpoint hit by the frontend every 2 seconds."""
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

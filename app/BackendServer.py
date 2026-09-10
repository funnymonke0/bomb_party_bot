import json
import logging
import os
import re
import shutil
import threading
import time

from pathlib import Path
from dataclasses import dataclass

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
from flask_talisman import Talisman
from bomb_party_bot.BotManager import BotManager
from flask import session
from dotenv import load_dotenv
import secrets

load_dotenv()



logger = logging.getLogger(__name__)
#!!!!! use same format as cli.py
root_dir = Path(__file__).resolve().parent
runtime_root = root_dir / "runtime"
config_root = root_dir.parent / "config"


BOT_TIMEOUT = 60*60 #60 min
HEARTBEAT_TIMEOUT = 10 #10s


@dataclass
class ClientSession:
    manager: BotManager | None = None
    bot_thread: threading.Thread | None = None
    last_heartbeat: float = 0.0
    heartbeat_active: bool = False
    start_time: float = 0.0
    runtime_dir: Path = runtime_root / "sid"

    @property
    def proxies(self):
        return str(self.runtime_dir / 'proxies.config')
    
    @property
    def settings(self):
        return str(self.runtime_dir / 'settings.json')

    @property
    def dictionaries(self):
        return str(self.runtime_dir / 'dictionaries.config')

    @property
    def invalid(self):
        return str(self.runtime_dir / 'invalid.config')


class BackendServer:
    def __init__(self, port = 5000, debug=False, force_https=True):
        self.app = Flask(__name__)
        frontend_origins = [origin.strip() for origin in os.getenv( #frontend in test is port 5173
            "FRONTEND_ORIGINS",
            "http://127.0.0.1:5173,http://localhost:5173"
        ).split(",") if origin.strip()]
        self.app.config.update(
            SECRET_KEY=os.environ["SECRET_KEY"],
            SESSION_COOKIE_HTTPONLY=True,
            SESSION_COOKIE_SECURE=force_https,  # HTTPS only when enabled
            SESSION_COOKIE_SAMESITE="Lax",
            MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 16 MB
        )
        Talisman(self.app, force_https=force_https)
        CORS(self.app, resources={r"/api/*": {"origins": frontend_origins}}, supports_credentials=True)
        self.lock = threading.RLock()
        self.port = port
        self.debug = debug
        self.sessions: dict[str, ClientSession] = {}
        runtime_root.mkdir(parents=True, exist_ok=True)

        self.csrf = CSRFProtect(self.app)
        self.limiter = Limiter(
            app=self.app,
            key_func=get_remote_address,
            default_limits=["60 per minute"],
            storage_uri=os.getenv("RATELIMIT_STORAGE_URI", "memory://")
        )



    def run(self):
        self._register_routes()
        global_monitor_thread = threading.Thread(target=self._check_heartbeat, daemon=True)
        global_monitor_thread.start()
        self.app.run(debug=self.debug, port=self.port, use_reloader=False)

    def _register_routes(self):
        #rate limiter wrapping. would be a decorator if not inside class
        home_wrapped = self.limiter.limit("60 per minute")(self.home)
        settings_wrapped = self.limiter.limit("30 per minute")(self.get_settings)
        launch_wrapped = self.limiter.limit("3 per minute")(self.launch_bot)
        stop_wrapped = self.limiter.limit("10 per minute")(self.stop_bot)
        heartbeat_wrapped = self.limiter.limit("120 per minute")(self.heartbeat)
        csrf_wrapped = self.limiter.limit("60 per minute")(self.get_csrf_token)
        # Maps endpoints directly to internal class methods.
        self.app.add_url_rule('/', 'home', home_wrapped)
        self.app.add_url_rule('/api/csrf', 'get_csrf_token', csrf_wrapped, methods=['GET'])
        self.app.add_url_rule('/api/settings', 'get_settings', settings_wrapped, methods=['GET'])
        self.app.add_url_rule('/api/launch', 'launch_bot', launch_wrapped, methods=['POST'])
        self.app.add_url_rule('/api/stop', 'stop_bot', stop_wrapped, methods=['POST'])
        self.app.add_url_rule('/api/heartbeat', 'heartbeat', heartbeat_wrapped, methods=['POST'])

    # endpoint
    def home(self) -> str:
        if "session_id" not in session:
            session["session_id"] = secrets.token_urlsafe(32)
        return render_template('index.html')

    def get_csrf_token(self):
        if "session_id" not in session:
            session["session_id"] = secrets.token_urlsafe(32)
        return jsonify({"csrfToken": generate_csrf()})

    def _get_or_create_client_locked(self, sid: str) -> ClientSession:
        if sid not in self.sessions:
            client_runtime_dir = runtime_root / sid
            client_runtime_dir.mkdir(parents=True, exist_ok=True)
            self.sessions[sid] = ClientSession(runtime_dir=client_runtime_dir)
            self._ensure_client_runtime_files(self.sessions[sid])
        return self.sessions[sid]

    def _ensure_client_runtime_files(self, client: ClientSession):
        file_pairs = (
            (Path(client.settings), config_root / "settings.json"),
            (Path(client.dictionaries), config_root / "dictionaries.config"),
            (Path(client.invalid), config_root / "invalid.config"),
            (Path(client.proxies), config_root / "proxies.config"),
        )
        for target, source in file_pairs:
            if target.exists():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.exists():
                shutil.copy2(source, target)
            elif target.suffix == ".json":
                target.write_text("{}", encoding="utf-8")
            else:
                target.write_text("", encoding="utf-8")

    def get_client(self) -> ClientSession:#creates a new client session for each unique user session. This allows multiple users to run bots independently.
        sid = session.get("session_id")
        if sid is None:
            sid = secrets.token_urlsafe(32)
            session["session_id"] = sid
        with self.lock:
            return self._get_or_create_client_locked(sid)

    def _stop_client(self, client: ClientSession) -> str | None:
        with self.lock:
            if client.manager:
                try:
                    client.manager.close()  # Gracefully stop the existing bot manager (maybe closed already)
                except Exception as e:
                    logger.warning(f"Error while closing bot manager: {e}")
            if client.bot_thread and client.bot_thread.is_alive():
                client.bot_thread.join(timeout=5)  # Wait for the thread to finish, with a timeout
            if client.bot_thread and client.bot_thread.is_alive():
                logger.warning("Error stopping bot: Thread did not terminate")
                return "Error stopping bot. Bot did not terminate"

            client.manager = None
            client.bot_thread = None
            try:
                shutil.rmtree(client.runtime_dir)
            except Exception as e:
                logger.warning(f"Error while removing runtime directory: {e}")

        import gc
        gc.collect()
        time.sleep(0.1)  # Give a moment for resources to be released
        return None

    # endpoint
    def stop_bot(self): #verbose
        client = self.get_client()
        error = self._stop_client(client)
        if error:
            return jsonify({"success": False, "error": error}), 500
        return jsonify({"success": True, "message": "Bot stopped."})

    # endpoint
    def get_settings(self):
        client = self.get_client()
        self._ensure_client_runtime_files(client)
        settings = {}
        with open(client.settings, 'r') as f:
            settings = json.load(f)
        return jsonify(settings)


    # endpoint
    def launch_bot(self):
        try:
            # 1. Grab incoming data from the HTML form
            with self.lock:
                data = request.json or {}
                client = self.get_client()
                self._ensure_client_runtime_files(client)
                if client.manager:
                    self.stop_bot()

                if client.bot_thread and client.bot_thread.is_alive():
                    return jsonify({"success": False, "error": "Error launching bot: Previous bot is still running"}), 500


                req_format = {
                    "username": (str, lambda x: len(x) <= 30 and re.match(r"^[A-Za-z0-9_-]+$", x.strip())),
                    "roomcode": (str, lambda x: re.match(r"^[a-zA-Z]{4}$", x.strip())),
                    "invalid": (list, lambda x: (len(x) <= 100) and all(isinstance(i, str) and len(i) <= 100 for i in x)),
                    "dictionaries": (list, lambda x: (len(x) <= 2000) and all(isinstance(i, str) and len(i) <= 100 for i in x)),
                    "proxies": (list, lambda x: (len(x) <= 100) and all(isinstance(i, str) and len(i) <= 100 for i in x)),
                    "selectMode": (str,None),
                    "regenIfNeeded": (bool,None),
                    "sneakyRegen": (bool,None),
                    "stockpile": (bool,None),
                    "greedLong": (bool,None),
                    "timeConstraint": (bool,None),
                    "cyberbullying": (bool,None),
                    "mistakes": (bool,None),
                    "burstType": (bool,None),
                    "spamType": (bool,None),
                    "dynamicRate": (bool,None),
                    "dynamicPauses": (bool,None),
                    "dynamicMistakes": (bool,None),
                    "minWait": (int|float,lambda x: x>=0 and x<=30),
                    "maxWait": (int|float,lambda x: x>=0 and x<=30),
                    "mistakePause": (int|float,lambda x: x>=0 and x<=30),
                    "miniPause": (int|float,lambda x: x>=0 and x<=30),
                    "minWpm": (int|float,lambda x: x>0 and x<1000),
                    "maxWpm": (int|float,lambda x: x>0 and x<1000),
                    "spamWpm": (int|float,lambda x: x>0 and x<2000),
                    "burstChance": (int|float,lambda x: x>=0 and x<=1),
                    "minMistakeChance": (int|float,lambda x: x>=0 and x<=1),
                    "maxMistakeChance": (int|float,lambda x: x>=0 and x<=1),
                    "spamChance": (int|float,lambda x: x>=0 and x<=1),
                    "jitterPercent": (int|float,lambda x: x>=0 and x<=1)
                }

                for key, (expected_type, req_func) in req_format.items():
                    if key not in data:
                        return jsonify({"success": False, "error": f"Missing key in data: {key}"}), 400
                    if not isinstance(data[key], expected_type):
                        expected_name = getattr(expected_type, "__name__", str(expected_type))
                        return jsonify({"success": False,
                            "error": f"Incorrect type for key in data: {key}. Expected {expected_name}"}), 400
                    if req_func and not req_func(data[key]):
                        return jsonify({"success": False,
                            "error": f"Invalid value for key in data: {key}"}), 400

                settings = {}
                with open(client.settings, 'r') as f:
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
                with open(client.settings, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=4)
                logger.info(f"--> [SUCCESS] settings.json updated")

                if dictionaries and len(dictionaries) > 0:
                    with open(client.dictionaries, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(dictionaries)+'\n')
                    logger.info(f"--> [SUCCESS] dictionaries.config updated")
                else:
                    logger.warning(f"--> [WARNING] No dictionaries provided, skipping update and using defaults.")

                if invalid and len(invalid) > 0:
                    with open(client.invalid, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(invalid)+'\n')
                    logger.info(f"--> [SUCCESS] invalid.config updated")
                else:
                    logger.warning(f"--> [WARNING] No invalid words provided, skipping update and using defaults.")

                if proxies and len(proxies) > 0:
                    with open(client.proxies, 'w', encoding='utf-8') as f:
                            f.write('\n'.join(proxies)+'\n')
                    logger.info(f"--> [SUCCESS] proxies.config updated")
                else:
                    logger.warning(f"--> [WARNING] No proxies provided, skipping update and using defaults (None).")


                # 4. Launch the bot in a separate thread to avoid blocking the Flask server
                client = self.get_client()
                client.manager = BotManager(
                    dict_file=client.dictionaries,
                    room_code=room_code,
                    proxy_file=client.proxies,
                    username=username,
                    settings_file=client.settings,
                    invalid_file=client.invalid,
                )
                client.bot_thread = threading.Thread(target=client.manager.persist_loop, daemon=True)
                client.bot_thread.start()
                client.start_time = time.time()

                client.last_heartbeat = time.time()

                return jsonify({"success": True, "message": "Configuration saved! Bot running."})

        except Exception as e:
            logger.error(f"--> [ERROR] {e}")
            return jsonify({"success": False, "error":"internal error occurred"}), 500 #server side error

    # endpoint
    def heartbeat(self):
        # Endpoint hit by the frontend every 2 seconds.
        with self.lock:
            client = self.get_client()
            client.last_heartbeat = time.time()
        return jsonify({"status": "alive"})

    def _check_heartbeat(self):

        while True:
            time.sleep(10)
            with self.lock:
                sessions = list(self.sessions.items())

            now = time.time()
            for sid, client in sessions:
                if now - client.last_heartbeat > HEARTBEAT_TIMEOUT:  # If no heartbeat for 10 seconds
                    self._stop_client(client)
                    with self.lock:
                        client.heartbeat_active = False
                        self.sessions.pop(sid, None)
                    continue
                if now - client.start_time > BOT_TIMEOUT:  # If bot has been running for too long
                    with self.lock:
                        client.start_time = now
                    self._stop_client(client)

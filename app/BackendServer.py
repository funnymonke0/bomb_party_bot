import json
import logging
import os
import re
import shutil

from functools import wraps
import time
import threading
from pathlib import Path
from dataclasses import dataclass

from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
from flask_talisman import Talisman
from flask import session
from dotenv import load_dotenv
import secrets
from .BotWorker import start_bot, worker_app


load_dotenv()



logger = logging.getLogger(__name__)
root_dir = Path(__file__).resolve().parent
runtime_root = root_dir / "runtime"
config_root = root_dir.parent / "config"

BOT_LIMIT = 20  #defines the concurrency

BOT_TIMEOUT = 30*60 #30 min
LAUNCH_COOLDOWN = 30 #seconds, may need to be increased
HEARTBEAT_TIMEOUT = 10 #10s

CSP = {
    'default-src': '\'self\'',
    'style-src': [
        '\'self\'',
        'https://unpkg.com',
        'https://cdn.jsdelivr.net',
        'https://googleapis.com'
    ],
    'font-src': [
        '\'self\'',
        'https://gstatic.com'
    ],
    'script-src': '\'self\''  # Keeping your scripts strictly local
}

@dataclass
class ClientSession:
    task_id : str | None = None
    last_heartbeat: float = 0.0
    heartbeat_active: bool = False
    start_time: float = 0.0
    runtime_dir: Path = runtime_root / "sid"
    last_launch_at: float = 0.0 #never

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

def handle_endpoint_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # exc_info=True prints the exact file, line number, and traceback
            logger.error(f"Unhandled exception in endpoint '{func.__name__}': {str(e)}", exc_info=True)

            # Return a generic, safe response to the user
            return jsonify({
                "status": "Error",
                "message": "An internal server error occurred."
            }), 500

    return wrapper

class BackendServer:

    def __init__(self, port = 5000, debug=False, force_https=True) -> None:
        frontend_origins = [origin.strip() for origin in os.getenv(
            "FRONTEND_ORIGINS",
            "http://127.0.0.1:5173,http://localhost:5173" # default for default purposes :)
        ).split(",") if origin.strip()]
        redis = os.getenv("RATELIMIT_STORAGE_URI", "redis://localhost:6379/0")
        self.app = Flask(__name__)
        self.app.config.update(
            SECRET_KEY=os.environ["SECRET_KEY"],
            SESSION_COOKIE_HTTPONLY=True,
            SESSION_COOKIE_SECURE=force_https,  # HTTPS only when enabled
            SESSION_COOKIE_SAMESITE="Lax",
            MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 16 MB
        )
        Talisman(self.app, force_https=force_https, content_security_policy=CSP)
        CORS(self.app, resources={r"/api/*": {"origins": frontend_origins}}, supports_credentials=True)
        self.port = port
        self.debug = debug
        self.sessions: dict[str, ClientSession] = {}
        runtime_root.mkdir(parents=True, exist_ok=True)

        self.csrf = CSRFProtect(self.app)
        self.limiter = Limiter(
            app=self.app,
            key_func=get_remote_address,
            default_limits=["60 per minute"],
            storage_uri= redis
        )
        self.app.register_error_handler(429, self._handle_rate_limit)
        self.bots_alive = 0


    def run(self) -> None:
        self._register_routes()
        global_monitor_thread = threading.Thread(target=self._check_heartbeat, daemon=True)
        global_monitor_thread.start()
        self.app.run(debug=self.debug, port=self.port, use_reloader=False)


    def register_routes(self) -> None:
        self._register_routes()


    def _register_routes(self) -> None:
        #rate limiter wrapping. would be a decorator if not inside class
        home_wrapped = self.limiter.limit("60 per minute")(handle_endpoint_errors(self.home))
        settings_wrapped = self.limiter.limit("30 per minute")(handle_endpoint_errors(self.get_settings))
        launch_wrapped = self.limiter.limit("3 per minute")(handle_endpoint_errors(self.launch_bot))
        stop_wrapped = self.limiter.limit("10 per minute")(handle_endpoint_errors(self.stop_bot))
        heartbeat_wrapped = self.limiter.limit("120 per minute")(handle_endpoint_errors(self.heartbeat))
        csrf_wrapped = self.limiter.limit("60 per minute")(handle_endpoint_errors(self.get_csrf_token))
        # Maps endpoints directly to internal class methods.
        self.app.add_url_rule('/', 'home', home_wrapped)#auto
        self.app.add_url_rule('/api/csrf', 'get_csrf_token', csrf_wrapped, methods=['GET'])#auto
        self.app.add_url_rule('/api/settings', 'get_settings', settings_wrapped, methods=['GET'])#auto
        self.app.add_url_rule('/api/launch', 'launch_bot', launch_wrapped, methods=['POST'])#user
        self.app.add_url_rule('/api/stop', 'stop_bot', stop_wrapped, methods=['POST'])#user
        self.app.add_url_rule('/api/heartbeat', 'heartbeat', heartbeat_wrapped, methods=['POST'])#auto


    def _handle_rate_limit(self, error):
        if request.path.startswith("/api/"):
            message = getattr(error, "description", None) or "Too Many Requests"
            return jsonify({"success": False, "error": "You are sending too many requests."}), 429
        return error


    # endpoint
    def home(self) -> str:
        if "session_id" not in session:
            session["session_id"] = secrets.token_urlsafe(32)
        return render_template('index.html')


    #endpoint
    def get_csrf_token(self) -> Response:
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


    def _ensure_client_runtime_files(self, client: ClientSession) -> None:
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
        return self._get_or_create_client_locked(sid)

    # endpoint
    def get_settings(self) -> Response:
        client = self.get_client()
        self._ensure_client_runtime_files(client)
        settings = {}
        with open(client.settings, 'r') as f:
            settings = json.load(f)
        return jsonify(settings)


    def _internal_stop_bot(self, client: ClientSession) -> None:
        if self._is_alive(client):
            worker_app.control.revoke(client.task_id, terminate = True, signal = "SIGTERM")
            client.start_time = time.time()  # resets the now-start_time tracking
            client.last_launch_at = 0.0  # last launched never
            client.task_id = None

    # endpoint
    def stop_bot(self) -> tuple[Response, int] | Response: #verbose
        client = self.get_client()
        if not self._is_alive(client):
            return jsonify({"success": False, "error": "No bot is currently running."}), 400
        else:
            self._internal_stop_bot(client)
        return jsonify({"success": True, "message": "Bot stopped."})

    # endpoint
    def launch_bot(self) -> tuple[Response, int] | Response:
        # 1. Grab incoming data from the HTML form
        self.update_alive()

        if self.bots_alive >= BOT_LIMIT:
            return jsonify(
                {"success": False,
                 "error": f"Global bot limit reached {self.bots_alive}/{BOT_LIMIT}. Please wait until resources free up."}), 429

        client = self.get_client()
        now = time.time()
        remaining = LAUNCH_COOLDOWN - (now - client.last_launch_at)
        if remaining > 0:
            return jsonify({"success": False, "error": f"Please wait {remaining:.2f} seconds between launches."}), 429

        if client.task_id is not None:
            remaining = BOT_TIMEOUT - (now-client.start_time)
            return jsonify({"success": False, "error": f"A bot is already running for this session with {remaining:.2f} seconds remaining. Please stop it before launching a new one."}), 400

        #too lazy to organize parsing into another func
        self._ensure_client_runtime_files(client)
        data = request.json or {}

        req_format = {
            "username": (str, lambda x: x == "" or (len(x) <= 30 and re.match(r"^[A-Za-z0-9_-]+$",x.strip()))),
            "roomcode": (str, lambda x: re.match(r"^[a-zA-Z]{4}$", x.strip())),
            "invalid": (list, lambda x: (len(x) <= 100) and all(isinstance(i, str) and len(i) <= 100 for i in x)),
            "dictionaries": (list, lambda x: (len(x) <= 2000) and all(isinstance(i, str) and len(i) <= 100 for i in x)),
            # "proxies": (list, lambda x: (len(x) <= 100) and all(isinstance(i, str) and len(i) <= 100 for i in x)),
            "selectMode": (str,None),#no validation needed, its a dropdown
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
            "minWait": (int|float,lambda x: 0 <= x <= 30),
            "maxWait": (int|float,lambda x: 0 <= x <= 30),
            "mistakePause": (int|float,lambda x: 0 <= x <= 30),
            "miniPause": (int|float,lambda x: 0 <= x <= 30),
            "minWpm": (int|float,lambda x: 0 < x < 1000),
            "maxWpm": (int|float,lambda x: 0 < x < 1000),
            "spamWpm": (int|float,lambda x: 0 < x < 2000),
            "burstChance": (int|float,lambda x: 0 <= x <= 1),
            "minMistakeChance": (int|float,lambda x: 0 <= x <= 1),
            "maxMistakeChance": (int|float,lambda x: 0 <= x <= 1),
            "spamChance": (int|float,lambda x: 0 <= x <= 1),
            "jitterPercent": (int|float,lambda x: 0 <= x <= 1)
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
        # proxies = data["proxies"]

        def get_val(setting:str):
            return data.get(setting) if isinstance(data.get(setting), req_format.get(setting)[0]) else settings.get(setting)
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



        # 4. Launch the bot in a separate background process to avoid blocking the Flask server
        client = self.get_client()
        task = start_bot.delay(dict_file = client.dictionaries, room_code = room_code, username = username, settings_file = client.settings, invalid_file = client.invalid)
        client.task_id = task.id
        client.start_time = time.time()
        client.last_launch_at = time.time()
        client.last_heartbeat = time.time()

        return jsonify({"success": True, "message": f"Configuration saved! Bot running. Bots timeout automatically after {BOT_TIMEOUT // 60} minutes."}), 200

    # endpoint
    def heartbeat(self) -> Response:
        # Endpoint hit by the frontend every 2 seconds.
        client = self.get_client()
        client.last_heartbeat = time.time()
        return jsonify({"status": "alive"})


    def check_heartbeat(self) -> None:
        self._check_heartbeat()  # Call the internal method to start the heartbeat check loop


    def _check_heartbeat(self) -> None:
        while True:
            time.sleep(10)

            sessions = list(self.sessions.items())

            now = time.time()

            for sid, client in sessions:

                if now - client.last_heartbeat > HEARTBEAT_TIMEOUT:  # If no heartbeat for 10 seconds
                    self._internal_stop_bot(client)
                    client.heartbeat_active = False
                    self.sessions.pop(sid, None)
                    continue # dont check timeout

                if now - client.start_time > BOT_TIMEOUT and self._is_alive(client):  # If bot has been running for too long

                    self._internal_stop_bot(client)
                    continue # here if anything else is added (will skip anything below if bot timeout is reached)


    def update_alive(self) -> None:
        sessions = list(self.sessions.items())
        self.bots_alive = 0
        for sid, client in sessions:

                if self._is_alive(client):
                    self.bots_alive += 1
                else:
                    # this is for when it exits on its own
                    client.start_time = time.time()  # resets the now-start_time tracking
                    client.last_launch_at = 0.0  # last launched never
                    client.task_id = None



    def _is_alive(self, client) -> bool:
        if client.task_id is not None:
            status = worker_app.AsyncResult(client.task_id).status
            return status in ['PENDING', 'RECEIVED', 'STARTED']
        return False
#evil deployment server

from app import BackendServer
import threading
import os

force_https = os.getenv("FORCE_HTTPS", "true").lower() == "true"
server = BackendServer(port=8000, force_https=force_https)
server.register_routes()
global_monitor_thread = threading.Thread(target=server.check_heartbeat, daemon=True)
global_monitor_thread.start()
app = server.app
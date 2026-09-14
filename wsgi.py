#evil deployment server

from app import BackendServer
import threading

server = BackendServer(port=5000, force_https=False)
server.register_routes()
global_monitor_thread = threading.Thread(target=server.check_heartbeat, daemon=True)
global_monitor_thread.start()
app = server.app
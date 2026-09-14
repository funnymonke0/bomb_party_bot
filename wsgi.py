#evil deployment server

from app import BackendServer

server = BackendServer(port=5000, force_https=False)
app = server.app
server._register_routes()
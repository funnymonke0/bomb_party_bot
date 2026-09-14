#evil deployment server

from app import BackendServer

server = BackendServer(port=5000, force_https=False)
server.register_routes()
app = server.app
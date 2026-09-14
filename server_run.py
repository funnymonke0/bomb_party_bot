from app import BackendServer
import os
# if __name__ == '__main__':
#     # Runs web server locally on http://127.0.0.1:5000
#     server = BackendServer(port=5000, force_https=False)#false in test
#     server.run()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    server = BackendServer(port=port, force_https=False)
    server.run()

from app import BackendServer

if __name__ == '__main__':
    # Runs web server locally on http://127.0.0.1:5000
    server = BackendServer(port=5000, force_https=False)
    server.run()
import threading
from mitmproxy.options import Options
from mitmproxy.tools.dump import DumpMaster
import asyncio
import time

class ProxyServer:
    def __init__(self, proxy:str=""):
        self.loop = None
        self.thread = None
        self.mitm = None
        self.proxyserver=None

        # "user:pass"
        proxy = proxy.removeprefix("https://")
        if "@" in proxy:
            self.userpass, self.hostport = proxy.split('@')
        else:
            self.hostport = proxy
            self.userpass = None
        # SPEC is host specification in the form of "http[s]://host[:port]", "upstream:SPEC"
        self.options = Options(
            listen_host='127.0.0.1',
            listen_port=0,
            mode = [f'upstream:http://{self.hostport}'],
            ssl_insecure=True,
        )


    def start(self) -> None:
        try:
            self.thread = threading.Thread(target=self._run_in_thread, daemon=True)
            self.thread.start()
            timeout = 3.0
            start_time = time.time()
            while self.proxyserver is None or not self.proxyserver.listen_addrs():
                if time.time() - start_time > timeout:
                    print("Timeout waiting for proxy socket to bind!")
                    break
                time.sleep(0.05)
        except Exception as e:
            print(f"Error starting proxy thread: {e}")

    def info(self) -> tuple[str, int]:
        if self.proxyserver:
            addrs = self.proxyserver.listen_addrs()
            if addrs and len(addrs) > 0:
                addr_tuple = addrs[0]
                if len(addr_tuple) > 1:
                    #host, port
                    return addr_tuple[0], addr_tuple[1]
                else:
                    print("problem resolving port")
        print("defaulting")
        return "" , 0

    async def _async_start(self):
        self.mitm = DumpMaster(self.options)
        self.mitm.options.set("termlog_verbosity=error")  # Mutes console event logging
        self.mitm.options.set("flow_detail=0")
        if self.userpass and len(self.userpass) > 0:
            self.mitm.options.upstream_auth = self.userpass
        self.proxyserver = self.mitm.addons.get("proxyserver")

        await self.mitm.run()

    def _run_in_thread(self) -> None:
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            self.loop.run_until_complete(self._async_start())
        except Exception as e:
            print(f"Error running async start: {e}")
        finally:
            try:
                self.loop.close()
            except Exception as e:
                print(f"Error closing loop: {e}")

    def close(self):
        if self.loop and self.mitm:
            try:
                self.loop.call_soon_threadsafe(self.mitm.shutdown)
            except Exception as e:
                print(f"Error closing loop: {e}")
        if self.thread:
            try:
                self.thread.join(timeout=2.0)
            except Exception as e:
                print(f"Error joining thread: {e}")



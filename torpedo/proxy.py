import os
import uuid
from subprocess import Popen
import time
from stem.control import Controller
from stem import Signal

import requests

from torpedo.linux_utils import get_free_port


class TorpedoProxy:
    def __init__(self):
        port = get_free_port()
        port_controller = get_free_port()
        container_name = f"torpedo_{uuid.uuid4().hex}"
        p = Popen(
            [
                "docker",
                "run",
                "-d",
                "--rm",
                "--name",
                container_name,
                "--publish",
                f"127.0.0.1:{port}:9050",
                "--expose",
                "9051",
                "--publish",
                f"127.0.0.1:{port_controller}:9051",
                "mipo57/tor-simple"
            ]
        )
        p.wait(timeout=20)

        self.process = p
        self.container_name = container_name
        self.port = port
        self.port_controller = port_controller

        self.deleted = False

    def address(self) -> str:
        return f"socks5://localhost:{self.port}"

    def reset_ip(self):
        with Controller.from_port(port = self.port_controller) as controller:
            controller.authenticate(password="test")
            controller.signal(Signal.NEWNYM)

    def delete(self):
        if not self.deleted:
            self.process.kill()
            Popen(
                ["docker", "kill", self.container_name]
            ).wait(timeout=20)
            self.deleted = True


class ProxiedSession(requests.Session):
    def set_proxy(self, proxy):
        self.torpedo_proxy = proxy

    def close(self) -> None:
        self.torpedo_proxy.delete()

        return super().close()

    def reset_ip(self):
        if self.torpedo_proxy:
            self.torpedo_proxy.reset_ip()

    def __exit__(self, *args) -> None:
        self.torpedo_proxy.delete()

        return super().__exit__(*args)


def new_session(timeout: float = 10.0, max_retries=5
) -> ProxiedSession:
    for _ in range(max_retries):
        new_proxy = TorpedoProxy()

        session = ProxiedSession()
        session.proxies = {"http": new_proxy.address().strip(), "https": new_proxy.address().strip()}

        session.set_proxy(new_proxy)

        if _wait_for_startup(new_proxy, timeout):
            return session
        else:
            session.close()

    return None


def _wait_for_startup(
    proxy: TorpedoProxy, timeout: float
) -> bool:
    max_time = time.time() + timeout

    now = time.time()
    while now < max_time:
        res = os.system(
            f"curl --max-time {int(max(max_time - time.time(), 1))} -s --socks5 127.0.0.1:{proxy.port} 'https://check.torproject.org/' |"
            " grep -qm1 Congratulations"
        )

        if res == 0:
            return True

        time.sleep(0.1)
        now = time.time()

    return False

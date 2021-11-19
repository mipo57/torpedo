import os
import signal
import subprocess
import uuid
from subprocess import PIPE, Popen
from typing import List
import time

import requests

from torpedo.linux_utils import get_free_port, set_pdeathsig


class TorpedoProxy:
    def __init__(self):
        p = subprocess.Popen(
            ["/usr/bin/docker", "pull" "osminogin/tor-simple"], preexec_fn=set_pdeathsig(signal.SIGKILL))
        p.wait()

        port = get_free_port()
        container_name = f"torpedo_{uuid.uuid4().hex}"
        p = subprocess.Popen(["/usr/bin/docker", "run", '-d', '--rm', "--name", container_name, "--publish",
                              f"127.0.0.1:{port}:9050", "osminogin/tor-simple"], preexec_fn=set_pdeathsig(signal.SIGKILL))
        p.wait()

        self.process = p
        self.container_name = container_name
        self.port = port

        self.deleted = False

    def address(self) -> str:
        return f"socks5://localhost:{self.port}"

    def delete(self):
        if not self.deleted:
            self.process.kill()
            subprocess.Popen(["docker", "container", "kill",
                              self.container_name]).wait()
            subprocess.Popen(["docker", "container", "rm",
                              self.container_name]).wait()


class ProxiedSession(requests.Session):
    def set_proxy(self, proxy):
        self.torpedo_proxy = proxy

    def close(self) -> None:
        self.torpedo_proxy.delete()

        return super().close()

    def __exit__(self, *args) -> None:
        self.torpedo_proxy.delete()

        return super().__exit__(*args)


def new_session(pause: float = 0.2, timeout: float = 5.0, max_retries=5) -> ProxiedSession:
    new_proxy = TorpedoProxy()

    session = ProxiedSession()
    session.proxies = {
        'http': new_proxy.address(),
        'https': new_proxy.address()
    }

    session.set_proxy(new_proxy)

    if _wait_for_startup(new_proxy, pause, timeout, max_retries):
        return session
    else:
        session.close()
        raise RuntimeError("Could not start a session")


def _wait_for_startup(proxy: TorpedoProxy, pause: float = 0.2, timeout: float = 5.0, max_retries=5) -> bool:

    timeout = time.time()  + timeout
    while time.time() < timeout:
        res = os.system(f"curl -s --socks5 127.0.0.1:{proxy.port} 'https://check.torproject.org/' | grep -qm1 Congratulations")

        if res == 0:
            return True

        time.sleep(0.1)

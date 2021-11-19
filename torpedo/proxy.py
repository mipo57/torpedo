import signal
import subprocess
import uuid
from subprocess import Popen
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
        p = subprocess.Popen(["/usr/bin/docker", "run", "--name", container_name, "--publish",
                              f"127.0.0.1:{port}:9050", "osminogin/tor-simple"], preexec_fn=set_pdeathsig(signal.SIGKILL))

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

    if _wait_for_startup(session, pause, timeout, max_retries):
        return session
    else:
        session.close()
        raise RuntimeError("Could not start a session")


def _wait_for_startup(session: ProxiedSession, pause: float = 0.2, timeout: float = 5.0, max_retries=5) -> bool:
    success = False

    for _ in range(max_retries):
        if success:
            return True

        try:
            time.sleep(pause)
            res = session.get('http://google.com', timeout=timeout)

            if res.status_code == 200:
                return True
        except:
            success = False

    return success

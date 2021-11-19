import signal
import ctypes
import socket

def set_pdeathsig(sig=signal.SIGKILL):
    """help function to ensure once parent process exits, its childrent processes will automatically die
    """
    def callable():
        libc = ctypes.CDLL("libc.so.6")
        return libc.prctl(1, sig)
    return callable

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("",0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port

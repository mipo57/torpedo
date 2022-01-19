from typing import Optional
import requests
import torpedo.proxy
from fake_useragent import UserAgent


class TorpedoSession:
    def __init__(self, timeout=10.0, max_retries=5, retry_codes=[]) -> None:
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_codes = retry_codes
        self.session = torpedo.proxy.new_session(timeout=timeout, max_retries=max_retries)

    def get(self, *args, **kwargs) -> Optional[requests.Response]:
        for _ in range(self.max_retries):
            if self.session is None:
                self.session = torpedo.proxy.new_session()

            if self.session is None:
                print("DUPA")
                continue

            headers = {'User-Agent': UserAgent().random}

            try:
                # print(kwargs)
                # # kwargs['timeout'] = kwargs.get('timeout', self.timeout)
                # # kwargs['headers'] = kwargs.get('headers', {})
                # # kwargs['headers']['User-Agent'] = kwargs['headers'].get('User-Agent', headers['User-Agent'])
                # print(kwargs)
            
                request_result = self.session.get(*args, **kwargs)
                print(request_result)
            except Exception as e:
                print(e)
                print("DDD")
                self.session.reset_ip()
                continue
            
            if request_result.status_code not in self.retry_codes:
                return request_result
            else:
                self.session.close()
                self.session = torpedo.proxy.new_session()

        return None

    def close(self) -> None:
        if self.session is not None:
            self.session.close()

        self.session = None

    def __del__(self) -> None:
        self.close()
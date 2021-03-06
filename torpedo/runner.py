from typing import Callable, List, Optional, Union
from multiprocessing import Process, Queue, set_start_method
from dataclasses import dataclass
import requests

from tqdm.std import trange
from torpedo.proxy import new_session
import tqdm
import time
from requests.exceptions import ConnectTimeout
from fake_useragent import UserAgent
import queue

@dataclass
class Task:
    id: int
    url: Union[str, dict]
    num_attempts: int
    result: Optional[dict]
    termination_task: bool

def process_tasks(
    task_queue,
    results_queue,
    parsing_func: Callable,
    max_attempts: int,
    request_timeout: float,
    repeat_parsing_errors: bool,
    use_session_cookies: bool = True,
    always_retry_codes: List[int] = [],
    verbose: bool = False,
):
    session = None

    while True:
        task = task_queue.get()

        if task.termination_task:
            break

        if session is None:
            session = new_session()

        if session is None:
            print("Failed to start a session, restarting...")
            task_queue.add(task)
            continue

        task.result = None
        task.num_attempts += 1

        headers = {'User-Agent': UserAgent().random}

        try:
            if not use_session_cookies:
                session.coookies.clear()

            if isinstance(task.url, str):
                request_result = session.get(task.url, timeout=request_timeout, headers=headers)
            else:
                task.url['timeout'] = task.url.get('timeout', request_timeout)
                task.url['headers'] = task.url.get('headers', {})
                task.url['headers']['User-Agent'] = task.url['headers'].get('User-Agent', headers['User-Agent'])
        
                request_result = session.get(**task.url)
        except Exception as e:
            print(e)
            if task.num_attempts < max_attempts:
                task_queue.put(task)
            else:
                results_queue.put(task)

            session.reset_ip()
            continue
        
        if request_result.status_code == 200:
            try:
                task.result = parsing_func(request_result.content)
            except Exception as e:
                print(f"Failed to parse {task.url}")
                print(e)
                if repeat_parsing_errors and task.num_attempts < max_attempts:
                    task_queue.put(task)
                else:
                    results_queue.put(task)

                continue
        elif request_result.status_code == 404:
            print(f"Link {task.url} returned with {request_result.status_code}")
            results_queue.put(task)
            continue
        elif request_result.status_code in always_retry_codes:
            if verbose:
                print(f"Encounder error code {request_result.status_code}. Retrying without increasing attempts!")
            session.reset_ip()
            task.num_attempts -= 1
            task_queue.put(task)
            continue

        results_queue.put(task)

    if session is not None:
        session.close()

    print("TASK FNISHED")


def run(
    scraping_func: Callable,
    urls: Union[List[str], List[dict]],
    num_workers: int = 1,
    max_attempts: int = 5,
    request_timeout: float = 15.0,
    repeat_parsing_errors: bool = False,
    use_session_cookies: bool = True,
    always_retry_codes: List[int] = [],
    verbose: bool = False,
):
    task_queue = Queue()
    results_queue = Queue()

    for id, url in enumerate(urls):
        task_queue.put(Task(id, url, 0, None, False))

    # For some reason logging with tqdm in main process is bugged
    processes = []

    for _ in range(num_workers):
        p = Process(
            target=process_tasks,
            args=(
                task_queue,
                results_queue,
                scraping_func,
                max_attempts,
                request_timeout,
                repeat_parsing_errors,
                use_session_cookies,
                always_retry_codes,
                verbose
            ),
            daemon=True
        )
        processes.append(p)
        p.start()

    output = [None] * len(urls)
    for _ in trange(len(urls)):
        entry = results_queue.get()
        output[entry.id] = entry.result

    for p in processes:
        task_queue.put(Task(-1, None, 0, None, True))

    for p in processes:
        p.join()

    return output

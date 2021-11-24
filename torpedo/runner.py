from typing import Callable, List, Optional
from multiprocessing import Process, Queue, set_start_method
from dataclasses import dataclass

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
    url: str
    num_attempts: int
    result: Optional[dict]

def process_tasks(
    task_queue,
    results_queue,
    parsing_func: Callable,
    max_attempts: int,
    request_timeout: float,
    repeat_parsing_errors: bool,
):
    session = None

    while True:
        try:
            task = task_queue.get_nowait()
        except queue.Empty:
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
            request_result = session.get(task.url, timeout=request_timeout, headers=headers)
        except:
            if task.num_attempts < max_attempts:
                task_queue.put(task)
            else:
                results_queue.put(task)

            session.reset_ip()
            continue
        
        if request_result.status_code == 200:
            try:
                task.result = parsing_func(request_result.content)
            except:
                print(f"Failed to parse {task.url}")
                if repeat_parsing_errors and task.num_attempts < max_attempts:
                    task_queue.put(task)
                else:
                    results_queue.put(task)
                continue
        elif request_result.status_code == 404:
            print(f"Link {task.url} returned with 404")
            results_queue.put(task)
            task_queue
            continue

        results_queue.put(task)

    if session is not None:
        session.close()

    print("TASK FNISHED")

def log_progress(num_tasks, task_queue, results_queue):
    pbar = tqdm.tqdm(total=num_tasks)

    while results_queue.qsize() < num_tasks:
        pbar.update(results_queue.qsize() - pbar.n)
        time.sleep(0.1)

    pbar.update(num_tasks - pbar.n)
    pbar.close()

    print("Logging FNISHED")

def run(
    scraping_func: Callable,
    urls: List[str],
    num_workers: int = 1,
    max_attempts: int = 5,
    request_timeout: float = 15.0,
    repeat_parsing_errors: bool = False,
):
    task_queue = Queue()
    results_queue = Queue()

    for id, url in enumerate(urls):
        task_queue.put(Task(id, url, 0, None))

    # For some reason logging with tqdm in main process is bugged
    processes = []
    # p = Process(target=log_progress, args=(len(urls), task_queue, results_queue), daemon=True)
    # processes.append(p)
    # p.start()

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
        p.join()

    return output

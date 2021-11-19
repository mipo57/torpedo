from typing import Callable, List, Optional
from multiprocessing import Process, Queue
from dataclasses import dataclass
from torpedo.proxy import new_session
import tqdm

@dataclass
class Task:
    url: str
    num_attempts: int
    result: Optional[dict]

def process_tasks(task_queue, results_queue, scraping_func: Callable, max_attempts: int, request_timeout: float):
    session = None

    while not task_queue.empty():
        task = task_queue.get()

        try:
            if session is None:
                session = new_session()

            request_result = session.get(task.url, timeout=request_timeout)
            if request_result.status_code == 200:
                task.result = scraping_func(request_result.content)
            else:
                task.result = None
        except:
            session.close()
            session = new_session()
            task.result = None

        task.num_attempts += 1

        if task.result is None and task.num_attempts < max_attempts:
            task_queue.put(task)
        else:
            results_queue.put(task)

    session.close()
    return True

def log_progress(num_tasks, task_queue):
    pbar = tqdm.tqdm(total = num_tasks)

    while not task_queue.empty():
        left = task_queue.qsize()

        progress = num_tasks - left
        pbar.update(progress - pbar.n)

    pbar.close()

    return True

def run(scraping_func: Callable, urls: List[str], num_workers: int = 1, max_attempts: int = 5, request_timeout: float = 5.0):
    task_queue = Queue()
    results_queue = Queue()

    for url in urls:
        task_queue.put(Task(url, 0, None))

    processes = []
    p = Process(target=log_progress, args=(len(urls), task_queue))
    processes.append(p)
    p.start()

    for _ in range(num_workers):
        p = Process(target=process_tasks, args=(task_queue, results_queue, scraping_func, max_attempts, request_timeout))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    output = []
    while not results_queue.empty():
        print("1")
        entry = results_queue.get()
        output.append(entry.result)

    print("DUPA")

    return output

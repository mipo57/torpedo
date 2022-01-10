# TORpedo
A simple python package to provide a TOR proxy for scraping sites

## Prerequisites
You need to have a docker installed on your system. Also, currently the package only works for linux

## Instalation
```bash
pip3 install git+https://github.com/mipo57/torpedo.git
```

## Proxy Usage

```python
import torpedo

with torpedo.new_session() as session:
    print(session.get("http://api.myip.com/").text)
```

The `session` object is derivative of `requests.Session` so u can use it exactly like you would use `requests.Session` normally. Mind that initialization (`torpedo.new_session()`) can take some time, so it's best to use single session for as long as possible. Also keep in mind that requests going through tor can be **MUCH** slower than direct ones. It's best to use this package in distributed context, where you would have number of scraping processes running in pararell, so that you don't wait too long for single request.

### How it works?
Under the hood, for every session new docker container is started. This docker container will provide a proxy that the http and https requests will go through.

## Runner Usage


```python
import torpedo

def scrape(request_result):
    # Your custom scraping function

    return {'price': 13, 'weight': 15, 'name': "meat"}


sites = [
    "https://example.com/example1",
    "https://example.com/example2",
    "https://example.com/example3",
    "https://example.com/example4"
]

torpedo.run(
    scraping_func = scrape,
    urls = sites,
    num_workers = 15,
    max_retries = 4,
    request_timeout = 5.0
)

# results = [
#   {'price': 13, 'weight': 15, 'name': "meat"},
#   {'price': 13, 'weight': 15, 'name': "meat"},
#   {'price': 13, 'weight': 15, 'name': "meat"},
#   {'price': 13, 'weight': 15, 'name': "meat"}
# ]
```



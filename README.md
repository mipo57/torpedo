# Torpedo
A simple python package to provide a TOR proxy for scraping sites

## Prerequisites
You need to have a docker installed on your system. Also, currently the package only works for linux
## How to use

```python
import torpedo

with torpedo.new_session() as session:
    print(session.get("http://api.myip.com/").text)
```

The `session` object is derivative of `requests.Session` so u can use it exactly like you would use `requests.Session` normally.

## How it works?
Under the hood, for every session new docker container is started. This docker container will provide a proxy that the http and https requests will go through.

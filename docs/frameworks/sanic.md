# Sanic

`aiodogstatsd` library can be easily used with [`Sanic`](https://sanicframework.org/) web framework by using listeners and middlewares provided.

At first you need to install `aiodogstatsd` with required extras:

```sh
pip install aiodogstatsd[sanic]
```

Then you can use code below as is to get initialized client and middlewares:

```python
from sanic import Sanic

from aiodogstatsd.contrib import sanic as aiodogstatsd


app = Sanic(name="aiodogstatsd")

listener_setup, listener_close = aiodogstatsd.listeners_factory()
app.register_listener(listener_setup, "before_server_start")
app.register_listener(listener_close, "after_server_stop")

middleware_req, middleware_resp = aiodogstatsd.middlewares_factory()
app.register_middleware(middleware_req, attach_to="request")
app.register_middleware(middleware_resp, attach_to="response")
```

Optionally you can provide additional configuration to the listeners factory:

- `client_app_key` — a key to store initialized `aiodogstatsd.Client` in application context (default: `statsd`);
- `host` — host string of your StatsD server (default: `localhost`);
- `port` — post of your StatsD server (default: `9125`);
- `namespace` — optional namespace string to prefix all metrics;
- `constant_tags` — optional tags dictionary to apply to all metrics;
- `read_timeout` (default: `0.5`);
- `close_timeout`;
- `sample_rate` (default: `1`).

Optionally you can provide additional configuration to the middlewares factory:

- `client_app_key` — a key to lookup `aiodogstatsd.Client` in application context (default: `statsd`);
- `request_duration_metric_name` — name of request duration metric  (default: `http_request_duration`);
- `collect_not_allowed` — collect or not `405 Method Not Allowed` responses;
- `collect_not_found` — collect or not `404 Not Found` responses.

# AIOHTTP

`aiodogstatsd` library can be easily used with [`AIOHTTP`](https://aiohttp.readthedocs.io/) web framework by using cleanup context and middleware provided.

At first you need to install `aiodogstatsd` with required extras:

```sh
pip install aiodogstatsd[aiohttp]
```

Then you can use code below as is to get initialized client and middleware:

```python
from aiohttp import web

from aiodogstatsd.contrib import aiohttp as aiodogstatsd


app = web.Application(middlewares=[aiodogstatsd.middleware_factory()])
app.cleanup_ctx.append(aiodogstatsd.cleanup_context_factory())
```

Optionally you can provide additional configuration to the cleanup context factory:

- `client_app_key` — a key to store initialized `aiodogstatsd.Client` in application context (default: `statsd`);
- `host` — host string of your StatsD server (default: `localhost`);
- `port` — post of your StatsD server (default: `9125`);
- `namespace` — optional namespace string to prefix all metrics;
- `constant_tags` — optional tags dictionary to apply to all metrics;
- `read_timeout` (default: `0.5`);
- `close_timeout`;
- `sample_rate` (default: `1`).

Optionally you can provide additional configuration to the middleware factory:

- `client_app_key` — a key to lookup `aiodogstatsd.Client` in application context (default: `statsd`);
- `request_duration_metric_name` — name of request duration metric  (default: `http_request_duration`);
- `collect_not_allowed` — collect or not `405 Method Not Allowed` responses;
- `collect_not_found` — collect or not `404 Not Found` responses.

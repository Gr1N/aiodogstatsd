# aiodogstatsd

[![Build Status](https://cloud.drone.io/api/badges/Gr1N/aiodogstatsd/status.svg)](https://cloud.drone.io/Gr1N/aiodogstatsd) [![codecov](https://codecov.io/gh/Gr1N/aiodogstatsd/branch/master/graph/badge.svg)](https://codecov.io/gh/Gr1N/aiodogstatsd) ![PyPI](https://img.shields.io/pypi/v/aiodogstatsd.svg?label=pypi%20version) ![PyPI - Downloads](https://img.shields.io/pypi/dm/aiodogstatsd.svg?label=pypi%20downloads) ![GitHub](https://img.shields.io/github/license/Gr1N/aiodogstatsd.svg)

An asyncio-based client for sending metrics to StatsD with support of [DogStatsD](https://docs.datadoghq.com/developers/dogstatsd/) extension.

Library fully tested with [statsd_exporter](https://github.com/prometheus/statsd_exporter) and supports `gauge`, `counter`, `histogram`, `distribution` and `timing` types.

## Installation

Just type:

```sh
$ pip install aiodogstatsd
```

...or if you're interested in integration with [`AIOHTTP`](https://aiohttp.readthedocs.io/) or [`Sanic`](https://sanicframework.org/) frameworks specify corresponding extras:

```sh
$ pip install aiodogstatsd[aiohttp,sanic]
```

## Usage

You can simply initialize client to send any metric you want:

```python
import asyncio

import aiodogstatsd


async def main():
    client = aiodogstatsd.Client()
    await client.connect()

    client.increment("users.online")

    await client.close()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
```

...or you can also use client as a context manager:

```python
import asyncio

import aiodogstatsd


async def main():
    async with aiodogstatsd.Client() as client:
      client.increment("users.online")


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
```

Look at `examples/` to find more examples of library usage, e.g. integration with [`AIOHTTP`](https://aiohttp.readthedocs.io/)  or [`Sanic`](https://sanicframework.org/) frameworks.

## Contributing

To work on the `aiodogstatsd` codebase, you'll want to clone the project locally and install the required dependencies via [poetry](https://poetry.eustace.io):

```sh
$ git clone git@github.com:Gr1N/aiodogstatsd.git
$ make install
```

To run tests and linters use command below:

```sh
$ make lint && make test
```

If you want to run only tests or linters you can explicitly specify which test environment you want to run, e.g.:

```sh
$ make lint-black
```

## License

`aiodogstatsd` is licensed under the MIT license. See the license file for details.

# aiodogstatsd

[![Build Status](https://github.com/Gr1N/aiodogstatsd/workflows/default/badge.svg)](https://github.com/Gr1N/aiodogstatsd/actions?query=workflow%3Adefault) [![codecov](https://codecov.io/gh/Gr1N/aiodogstatsd/branch/master/graph/badge.svg)](https://codecov.io/gh/Gr1N/aiodogstatsd) ![PyPI](https://img.shields.io/pypi/v/aiodogstatsd.svg?label=pypi%20version) ![PyPI - Downloads](https://img.shields.io/pypi/dm/aiodogstatsd.svg?label=pypi%20downloads) ![GitHub](https://img.shields.io/github/license/Gr1N/aiodogstatsd.svg)

An asyncio-based client for sending metrics to StatsD with support of [DogStatsD](https://docs.datadoghq.com/developers/dogstatsd/) extension.

Library fully tested with [statsd_exporter](https://github.com/prometheus/statsd_exporter) and supports `gauge`, `counter`, `histogram`, `distribution` and `timing` types.

`aiodogstatsd` client by default uses _9125_ port. It's a default port for [statsd_exporter](https://github.com/prometheus/statsd_exporter) and it's different from _8125_ which is used by default in StatsD and [DataDog](https://www.datadoghq.com/). Initialize the client with the proper port you need if it's different from _9125_.

## Installation

Just type:

```sh
$ pip install aiodogstatsd
```

## At a glance

Just simply use client as a context manager and send any metric you want:

```python
import asyncio

import aiodogstatsd


async def main():
    async with aiodogstatsd.Client() as client:
        client.increment("users.online")


asyncio.run(main())
```

Please follow [documentation](https://gr1n.github.io/aiodogstatsd) or look at [`examples/`](https://github.com/Gr1N/aiodogstatsd/tree/master/examples) directory to find more examples of library usage, e.g. integration with [`AIOHTTP`](https://aiohttp.readthedocs.io/) or [`Starlette`](https://www.starlette.io) frameworks.

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

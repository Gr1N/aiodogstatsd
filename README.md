# aiodogstatsd

An asyncio-based client for sending metrics to StatsD with support of [DogStatsD](https://docs.datadoghq.com/developers/dogstatsd/) extension.

Library fully tested with [statsd_exporter](https://github.com/prometheus/statsd_exporter) and supports `gauge`, `counter`, `histogram`, `distribution` and `timing` types.

## Installation

```sh
$ pip install aiodogstatsd
```

## Usage

```python
import asyncio

import aiodogstatsd


async def main():
    client = aiodogstatsd.Client()
    await client.connect()

    client.increment("users.online")

    await client.close()


asyncio.run(main())
```

Look at `examples/` to find more examples of library usage.

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

# Changelog for aiodogstatsd

## 0.16.0 (2021-12-12)

- Added Python 3.10.* support
- Dropped Sanic support
- Fixed AIOHTTP support, #30

## 0.15.0 (2020-12-21)

- Added `.timeit_task()`, `asyncio.create_task` like function that sends timing metric when the task finishes, #29 by @aviramha
- Added `threshold_ms` (Optional) to `.timeit()` for sending timing metric only when exceeds threshold, #27 by @aviramha

## 0.14.0 (2020-11-16)

- Added Python 3.9.* support
- Fixed `.timeit()` in case of unhandled exceptions, #26

## 0.13.0 (2020-07-29)

- Added configuration option to limit pending queue size. Can be configured by passing `pending_queue_size` named argument into `aiodogstatsd.Client` class. By default: `65536`, #24

## 0.12.0 (2020-05-29)

- Added `connected`, `closing` and `disconnected` client properties. Can be used to check connection state of client, #23
- Bumped minimum required `Sanic` version, #23

## 0.11.0 (2020-02-21)

- Updated documentation: described why 9125 port used by default, #16
- Added [`Starlette`](https://www.starlette.io) framework integration helpers (middleware), #15
- Fixed futures initialization. From this time futures always initialized in the same event loop, #15
- Added [documentation](https://gr1n.github.io/aiodogstatsd), #18

## 0.10.0 (2019-12-03)

- Fixed `MTags` type to be a `Mapping` to avoid common invariance type-checking errors, #14 by @JayH5

## 0.9.0 (2019-11-29)

- Added sample rate as class attribute, for setting sample rate class-wide, #11 by @aviramha
- Added timer context manager for easily timing events, #12 by @aviramha
- Added Python 3.8.* support, #7

## 0.8.0 (2019-11-03)

- Fixed `AIOHTTP` middleware to catch any possible exception, #6
- Fixed `AIOHTTP` middleware to properly handle variable routes, #8

## 0.7.0 (2019-08-14)

- Fixed `AIOHTTP` graceful shutdown, #5 by @Reskov

## 0.6.0 (2019-05-24)

- **Breaking Change:** Send time in milliseconds in middlewares, #3 by @eserge

## 0.5.0 (2019-05-16)

- Added [`AIOHTTP`](https://aiohttp.readthedocs.io/) framework integration helpers (cleanup context and middleware).
- Added [`Sanic`](https://sanicframework.org/) framework integration helpers (listeners and middlewares).

## 0.4.0 (2019-04-29)

- Added Python 3.6.* support.

## 0.3.0 (2019-04-21)

- Fixed datagram format.

## 0.2.0 (2019-04-06)

- Added possibility to use `aiodogstatsd.Client` as a context manager.

## 0.1.0 (2019-02-10)

- Initial release.

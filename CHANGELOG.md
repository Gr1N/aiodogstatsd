# Changelog for aiodogstatsd

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

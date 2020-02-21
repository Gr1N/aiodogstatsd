# Usage

## Basics

`aiodogstatsd.Client` can be initialized with:

- `host` — host string of your StatsD server (default: `localhost`);
- `port` — post of your StatsD server (default: `9125`);
- `namespace` — optional namespace string to prefix all metrics;
- `constant_tags` — optional tags dictionary to apply to all metrics;
- `read_timeout` (default: `0.5`);
- `close_timeout`;
- `sample_rate` (default: `1`).

Below you can find an example of client initialization. Keep your eyes on lines 13 and 15. You always need to not to forget to initialize connection and close it at the end:

```python hl_lines="13 15"
client = aiodogstatsd.Client(
    host="127.0.0.1",
    port=8125,
    namespace="hello",
    constant_tags={
        "service": "auth",
    },
    read_timeout=0.5,
    close_timeout=0.5,
    sample_rate=1,
)

await client.connect()
client.increment("users.online")
await client.close()
```

## Context manager

As an option you can use `aiodogstatsd.Client` as a context manager. In that case you don't need to remember to initialize and close connection:

```python
async with aiodogstatsd.Client() as client:
    client.increment("users.online")
```

## Sending metrics

### Gauge

Record the value of a gauge, optionally setting `tags` and a `sample_rate`.

```python
client.gauge("users.online", value=42)
```

### Increment

Increment a counter, optionally setting a `value`, `tags` and a `sample_rate`.

```python
client.increment("users.online")
```

### Decrement

Decrement a counter, optionally setting a `value`, `tags` and a `sample_rate`.

```python
client.decrement("users.online")
```

### Histogram

Sample a histogram value, optionally setting `tags` and a `sample_rate`.

```python
client.histogram("request.time", value=0.2)
```

### Distribution

Send a global distribution value, optionally setting `tags` and a `sample_rate`.

```python
client.distribution("uploaded.file.size", value=8819)
```

### Timing

Record a timing, optionally setting `tags` and a `sample_rate`.

```python
client.timing("query.time", value=0.5)
```

### TimeIt

Context manager for easily timing methods, optionally settings `tags` and a `sample_rate`.

```python
with client.timeit("query.time"):
    ...
```

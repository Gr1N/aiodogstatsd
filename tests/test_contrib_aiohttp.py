import asyncio
import sys
from http import HTTPStatus

import aiohttp
import pytest
from aiohttp import web
from yarl import URL

from aiodogstatsd.contrib import aiohttp as aiodogstatsd

pytestmark = pytest.mark.asyncio


def all_tasks():
    if sys.version_info >= (3, 7):
        return asyncio.all_tasks()
    else:
        tasks = list(asyncio.Task.all_tasks())
        return {t for t in tasks if not t.done()}


def current_task():
    if sys.version_info >= (3, 7):
        return asyncio.current_task()
    else:
        return asyncio.Task.current_task()


@pytest.fixture(autouse=True)
async def aiohttp_server(unused_tcp_port, unused_udp_port):
    async def handler_hello(request):
        return web.json_response({"hello": "aiodogstatsd"})

    async def handler_hello_variable(request):
        return web.json_response({"hello": request.match_info["name"]})

    async def handler_bad_request(request):
        return web.json_response({"hello": "bad"}, status=HTTPStatus.BAD_REQUEST)

    async def handler_internal_server_error(request):
        raise NotImplementedError()

    async def handler_unauthorized(request):
        raise web.HTTPUnauthorized()

    app = web.Application(middlewares=[aiodogstatsd.middleware_factory()])
    app.cleanup_ctx.append(
        aiodogstatsd.cleanup_context_factory(
            host="0.0.0.0", port=unused_udp_port, constant_tags={"whoami": "batman"}
        )
    )

    app.add_routes(
        [
            web.get("/hello", handler_hello),
            web.get("/hello/{name}", handler_hello_variable),
            web.post("/bad_request", handler_bad_request),
            web.get("/internal_server_error", handler_internal_server_error),
            web.get("/unauthorized", handler_unauthorized),
        ]
    )

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, host="0.0.0.0", port=unused_tcp_port)
    await site.start()
    yield
    await runner.cleanup()


@pytest.fixture
def aiohttp_server_url(unused_tcp_port):
    return URL(f"http://0.0.0.0:{unused_tcp_port}")


@pytest.fixture(autouse=True)
def mock_loop_time(mocker):
    mock_loop = mocker.Mock()
    mock_loop.time.side_effect = [0, 1]

    mocker.patch("aiodogstatsd.contrib.aiohttp.get_event_loop", return_value=mock_loop)


class TestAIOHTTP:
    async def test_ok(self, aiohttp_server_url, statsd_server, wait_for):
        udp_server, collected = statsd_server

        async with udp_server:
            async with aiohttp.ClientSession() as session:
                async with session.get(aiohttp_server_url / "hello") as resp:
                    assert resp.status == HTTPStatus.OK

            await wait_for(collected)

        assert collected == [
            b"http_request_duration:1000|ms"
            b"|#whoami:batman,method:GET,path:/hello,status:200"
        ]

    async def test_ok_variable_route(self, aiohttp_server_url, statsd_server, wait_for):
        udp_server, collected = statsd_server

        async with udp_server:
            async with aiohttp.ClientSession() as session:
                async with session.get(aiohttp_server_url / "hello" / "batman") as resp:
                    assert resp.status == HTTPStatus.OK

            await wait_for(collected)

        assert collected == [
            b"http_request_duration:1000|ms"
            b"|#whoami:batman,method:GET,path:/hello/{name},status:200"
        ]

    async def test_bad_request(self, aiohttp_server_url, statsd_server, wait_for):
        udp_server, collected = statsd_server

        async with udp_server:
            async with aiohttp.ClientSession() as session:
                async with session.post(aiohttp_server_url / "bad_request") as resp:
                    assert resp.status == HTTPStatus.BAD_REQUEST

            await wait_for(collected)

        assert collected == [
            b"http_request_duration:1000|ms"
            b"|#whoami:batman,method:POST,path:/bad_request,status:400"
        ]

    async def test_internal_server_error(
        self, aiohttp_server_url, statsd_server, wait_for
    ):
        udp_server, collected = statsd_server

        async with udp_server:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    aiohttp_server_url / "internal_server_error"
                ) as resp:
                    assert resp.status == HTTPStatus.INTERNAL_SERVER_ERROR

            await wait_for(collected)

        assert collected == [
            b"http_request_duration:1000|ms"
            b"|#whoami:batman,method:GET,path:/internal_server_error,status:500"
        ]

    async def test_unauthorized(self, aiohttp_server_url, statsd_server, wait_for):
        udp_server, collected = statsd_server

        async with udp_server:
            async with aiohttp.ClientSession() as session:
                async with session.get(aiohttp_server_url / "unauthorized") as resp:
                    assert resp.status == HTTPStatus.UNAUTHORIZED

            await wait_for(collected)

        assert collected == [
            b"http_request_duration:1000|ms"
            b"|#whoami:batman,method:GET,path:/unauthorized,status:401"
        ]

    async def test_not_allowed(self, aiohttp_server_url, statsd_server, wait_for):
        udp_server, collected = statsd_server

        async with udp_server:
            async with aiohttp.ClientSession() as session:
                async with session.post(aiohttp_server_url / "hello") as resp:
                    assert resp.status == HTTPStatus.METHOD_NOT_ALLOWED

            await wait_for(collected)

        assert collected == []

    async def test_not_found(self, aiohttp_server_url, statsd_server, wait_for):
        udp_server, collected = statsd_server

        async with udp_server:
            async with aiohttp.ClientSession() as session:
                async with session.get(aiohttp_server_url / "not_found") as resp:
                    assert resp.status == HTTPStatus.NOT_FOUND

            await wait_for(collected)

        assert collected == []

    @pytest.mark.timeout(10)
    async def test_client_closed_correctly(self):
        # Simulate actual behavior of the web.run_app clean up phase:
        # cancel all active tasks at the end
        # https://git.io/fj56P

        tasks = all_tasks()

        # cancel all tasks except current
        test_task = current_task()
        for task in tasks:
            if task is not test_task:
                task.cancel()

        # should not hang on the end

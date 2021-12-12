from http import HTTPStatus
from uuid import uuid4

import aiohttp
import pytest
from yarl import URL

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.filterwarnings("ignore:Using or importing the ABCs:DeprecationWarning"),
]


@pytest.fixture(autouse=True)
async def sanic_server(event_loop, unused_tcp_port, unused_udp_port):
    from sanic import Sanic, response
    from sanic.exceptions import Unauthorized

    from aiodogstatsd.contrib import sanic as aiodogstatsd

    async def handler_hello(request):
        return response.json({"hello": "aiodogstatsd"})

    async def handler_bad_request(request):
        return response.json({"hello": "bad"}, status=HTTPStatus.BAD_REQUEST)

    async def handler_internal_server_error(request):
        raise NotImplementedError()

    async def handler_unauthorized(request):
        raise Unauthorized("Unauthorized")

    app = Sanic(name=uuid4().hex)

    listener_setup_statsd, listener_close_statsd = aiodogstatsd.listeners_factory(
        host="0.0.0.0", port=unused_udp_port, constant_tags={"whoami": "batman"}
    )
    app.register_listener(listener_setup_statsd, "before_server_start")
    app.register_listener(listener_close_statsd, "after_server_stop")

    (
        middleware_request_statsd,
        middleware_response_statsd,
    ) = aiodogstatsd.middlewares_factory()
    app.register_middleware(middleware_request_statsd, attach_to="request")
    app.register_middleware(middleware_response_statsd, attach_to="response")

    app.add_route(handler_hello, "/hello")
    app.add_route(handler_bad_request, "/bad_request", methods={"POST"})
    app.add_route(handler_internal_server_error, "/internal_server_error")
    app.add_route(handler_unauthorized, "/unauthorized")

    server = await app.create_server(
        host="0.0.0.0", port=unused_tcp_port, return_asyncio_server=True
    )
    yield
    server.close()
    await server.wait_closed()
    await listener_close_statsd(app, event_loop)


@pytest.fixture
def sanic_server_url(unused_tcp_port):
    return URL(f"http://0.0.0.0:{unused_tcp_port}")


@pytest.fixture(autouse=True)
def mock_loop_time(mocker):
    mock_loop = mocker.Mock()
    mock_loop.time.side_effect = [0, 1]

    mocker.patch("aiodogstatsd.contrib.sanic.get_event_loop", return_value=mock_loop)


class TestSanic:
    async def test_ok(self, sanic_server_url, statsd_server, wait_for):
        udp_server, collected = statsd_server

        async with udp_server:
            async with aiohttp.ClientSession() as session:
                async with session.get(sanic_server_url / "hello") as resp:
                    assert resp.status == HTTPStatus.OK

            await wait_for(collected)

        assert collected == [
            b"http_request_duration:1000|ms"
            b"|#whoami:batman,method:GET,path:/hello,status:200"
        ]

    async def test_bad_request(self, sanic_server_url, statsd_server, wait_for):
        udp_server, collected = statsd_server

        async with udp_server:
            async with aiohttp.ClientSession() as session:
                async with session.post(sanic_server_url / "bad_request") as resp:
                    assert resp.status == HTTPStatus.BAD_REQUEST

            await wait_for(collected)

        assert collected == [
            b"http_request_duration:1000|ms"
            b"|#whoami:batman,method:POST,path:/bad_request,status:400"
        ]

    async def test_internal_server_error(
        self, sanic_server_url, statsd_server, wait_for
    ):
        udp_server, collected = statsd_server

        async with udp_server:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    sanic_server_url / "internal_server_error"
                ) as resp:
                    assert resp.status == HTTPStatus.INTERNAL_SERVER_ERROR

            await wait_for(collected)

        assert collected == [
            b"http_request_duration:1000|ms"
            b"|#whoami:batman,method:GET,path:/internal_server_error,status:500"
        ]

    async def test_unauthorized(self, sanic_server_url, statsd_server, wait_for):
        udp_server, collected = statsd_server

        async with udp_server:
            async with aiohttp.ClientSession() as session:
                async with session.get(sanic_server_url / "unauthorized") as resp:
                    assert resp.status == HTTPStatus.UNAUTHORIZED

            await wait_for(collected)

        assert collected == [
            b"http_request_duration:1000|ms"
            b"|#whoami:batman,method:GET,path:/unauthorized,status:401"
        ]

    async def test_not_allowed(self, sanic_server_url, statsd_server, wait_for):
        udp_server, collected = statsd_server

        async with udp_server:
            async with aiohttp.ClientSession() as session:
                async with session.post(sanic_server_url / "hello") as resp:
                    assert resp.status == HTTPStatus.METHOD_NOT_ALLOWED

            await wait_for(collected)

        assert collected == []

    async def test_not_found(self, sanic_server_url, statsd_server, wait_for):
        udp_server, collected = statsd_server

        async with udp_server:
            async with aiohttp.ClientSession() as session:
                async with session.get(sanic_server_url / "not_found") as resp:
                    assert resp.status == HTTPStatus.NOT_FOUND

            await wait_for(collected)

        assert collected == []

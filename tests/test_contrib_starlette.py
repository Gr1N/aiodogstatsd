from http import HTTPStatus

import pytest
from async_asgi_testclient import TestClient
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.responses import JSONResponse
from starlette.routing import Route

import aiodogstatsd
from aiodogstatsd.contrib.starlette import StatsDMiddleware

pytestmark = pytest.mark.asyncio


@pytest.fixture
def starlette_application(unused_udp_port):
    async def handler_hello(request):
        return JSONResponse({"hello": "aiodogstatsd"})

    async def handler_hello_variable(request):
        return JSONResponse({"hello": request.path_params["name"]})

    async def handler_bad_request(request):
        return JSONResponse({"hello": "bad"}, status_code=HTTPStatus.BAD_REQUEST)

    async def handler_internal_server_error(request):
        raise NotImplementedError()

    async def handler_unauthorized(request):
        raise HTTPException(HTTPStatus.UNAUTHORIZED)

    client = aiodogstatsd.Client(
        host="0.0.0.0", port=unused_udp_port, constant_tags={"whoami": "batman"}
    )

    return Starlette(
        debug=True,
        routes=[
            Route("/hello", handler_hello),
            Route("/hello/{name}", handler_hello_variable),
            Route("/bad_request", handler_bad_request, methods=["POST"]),
            Route("/internal_server_error", handler_internal_server_error),
            Route("/unauthorized", handler_unauthorized),
        ],
        middleware=[Middleware(StatsDMiddleware, client=client)],
        on_startup=[client.connect],
        on_shutdown=[client.close],
    )


@pytest.fixture(autouse=True)
def mock_loop_time(mocker):
    mock_loop = mocker.Mock()
    mock_loop.time.side_effect = [0, 1]

    mocker.patch(
        "aiodogstatsd.contrib.starlette.get_event_loop", return_value=mock_loop
    )


class TestStarlette:
    async def test_ok(self, starlette_application, statsd_server, wait_for):
        udp_server, collected = statsd_server

        async with udp_server:
            async with TestClient(starlette_application) as client:
                resp = await client.get("/hello")
                assert resp.status_code == HTTPStatus.OK

                await wait_for(collected)

        assert collected == [
            b"http_request_duration:1000|ms"
            b"|#whoami:batman,method:GET,path:/hello,status:200"
        ]

    async def test_ok_variable_route(
        self, starlette_application, statsd_server, wait_for
    ):
        udp_server, collected = statsd_server

        async with udp_server:
            async with TestClient(starlette_application) as client:
                resp = await client.get("/hello/batman")
                assert resp.status_code == HTTPStatus.OK

            await wait_for(collected)

        assert collected == [
            b"http_request_duration:1000|ms"
            b"|#whoami:batman,method:GET,path:/hello/{name},status:200"
        ]

    async def test_bad_request(self, starlette_application, statsd_server, wait_for):
        udp_server, collected = statsd_server

        async with udp_server:
            async with TestClient(starlette_application) as client:
                resp = await client.post("/bad_request")
                assert resp.status_code == HTTPStatus.BAD_REQUEST

            await wait_for(collected)

        assert collected == [
            b"http_request_duration:1000|ms"
            b"|#whoami:batman,method:POST,path:/bad_request,status:400"
        ]

    async def test_internal_server_error(
        self, starlette_application, statsd_server, wait_for
    ):
        udp_server, collected = statsd_server

        async with udp_server:
            async with TestClient(starlette_application) as client:
                # Here we can't check proper response status code due to realization of
                # test client.
                with pytest.raises(NotImplementedError):
                    await client.get("/internal_server_error")

            await wait_for(collected)

        assert collected == [
            b"http_request_duration:1000|ms"
            b"|#whoami:batman,method:GET,path:/internal_server_error,status:500"
        ]

    async def test_unauthorized(self, starlette_application, statsd_server, wait_for):
        udp_server, collected = statsd_server

        async with udp_server:
            async with TestClient(starlette_application) as client:
                resp = await client.get("/unauthorized")
                assert resp.status_code == HTTPStatus.UNAUTHORIZED

            await wait_for(collected)

        assert collected == [
            b"http_request_duration:1000|ms"
            b"|#whoami:batman,method:GET,path:/unauthorized,status:401"
        ]

    async def test_not_allowed(self, starlette_application, statsd_server, wait_for):
        udp_server, collected = statsd_server

        async with udp_server:
            async with TestClient(starlette_application) as client:
                resp = await client.post("/hello")
                assert resp.status_code == HTTPStatus.METHOD_NOT_ALLOWED

            await wait_for(collected)

        assert collected == []

    async def test_not_found(self, starlette_application, statsd_server, wait_for):
        udp_server, collected = statsd_server

        async with udp_server:
            async with TestClient(starlette_application) as client:
                resp = await client.get("/not_found")
                assert resp.status_code == HTTPStatus.NOT_FOUND

            await wait_for(collected)

        assert collected == []

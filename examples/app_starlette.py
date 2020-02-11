from http import HTTPStatus

import uvicorn
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

import aiodogstatsd
from aiodogstatsd.contrib.starlette import StatsDMiddleware


async def handler_hello(request: Request) -> JSONResponse:
    return JSONResponse({"hello": "aiodogstatsd"})


async def handler_bad_request(request: Request) -> JSONResponse:
    return JSONResponse({"hello": "bad"}, status_code=HTTPStatus.BAD_REQUEST)


async def handler_internal_server_error(request: Request) -> JSONResponse:
    raise NotImplementedError()


async def handler_unauthorized(request: Request) -> JSONResponse:
    raise HTTPException(HTTPStatus.UNAUTHORIZED)


def get_application() -> Starlette:
    client = aiodogstatsd.Client(
        host="0.0.0.0", port=9125, constant_tags={"whoami": "I am Batman!"}
    )

    app = Starlette(
        debug=True,
        routes=[
            Route("/hello", handler_hello),
            Route("/bad_request", handler_bad_request),
            Route("/internal_server_error", handler_internal_server_error),
            Route("/unauthorized", handler_unauthorized),
        ],
        middleware=[Middleware(StatsDMiddleware, client=client)],
        on_startup=[client.connect],
        on_shutdown=[client.close],
    )

    return app


if __name__ == "__main__":
    app = get_application()
    uvicorn.run(app)

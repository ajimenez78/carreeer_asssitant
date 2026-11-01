"""Origin enforcement, bounded request bodies, and private response caching."""

from starlette.datastructures import Headers

from career_assistant.errors import error_response


class RequestBoundary:
    def __init__(self, app, allowed_origins):
        self.app, self.allowed_origins = app, set(allowed_origins)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not scope["path"].startswith("/api/"):
            await self.app(scope, receive, send)
            return
        headers = Headers(scope=scope)
        if (
            scope["method"] not in {"GET", "HEAD", "OPTIONS"}
            and headers.get("origin") not in self.allowed_origins
        ):
            await error_response(
                "untrusted_origin",
                "Send writes from a configured application origin.",
                403,
            )(scope, receive, send)
            return
        limit = (
            10 * 1024 * 1024 + 64 * 1024
            if headers.get("content-type", "").startswith("multipart/form-data")
            else 256 * 1024
        )
        try:
            declared = int(headers.get("content-length", "0"))
        except ValueError:
            declared = -1
        if declared < 0 or declared > limit:
            await error_response(
                "request_too_large", "The request body exceeds its allowed size.", 413
            )(scope, receive, send)
            return
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            if len(body) + len(chunk) > limit:
                await error_response(
                    "request_too_large",
                    "The request body exceeds its allowed size.",
                    413,
                )(scope, receive, send)
                return
            body.extend(chunk)
            if not message.get("more_body", False):
                break

        payload = bytes(body)
        body.clear()

        async def bounded_receive():
            nonlocal payload
            if payload is None:
                return await receive()
            message = {"type": "http.request", "body": payload, "more_body": False}
            payload = None
            return message

        async def private_send(message):
            if message["type"] == "http.response.start":
                message["headers"] = [
                    *message.get("headers", []),
                    (b"cache-control", b"no-store"),
                    (b"x-content-type-options", b"nosniff"),
                ]
            await send(message)

        await self.app(scope, bounded_receive, private_send)

import asyncio

from presentation.middleware import RequestBodyLimit


def test_chunked_body_over_limit_is_rejected_before_application():
    async def scenario():
        messages = iter(
            [
                {"type": "http.request", "body": b"123", "more_body": True},
                {"type": "http.request", "body": b"456", "more_body": False},
            ]
        )
        responses = []

        async def receive():
            return next(messages)

        async def send(message):
            responses.append(message)

        async def forbidden(scope, receive, send):
            raise AssertionError("Oversized input must not reach the application")

        await RequestBodyLimit(forbidden, max_bytes=5)({"type": "http"}, receive, send)
        assert responses[0]["status"] == 413

    asyncio.run(scenario())


def test_bounded_chunked_body_is_replayed_unchanged():
    async def scenario():
        messages = iter(
            [
                {"type": "http.request", "body": b"12", "more_body": True},
                {"type": "http.request", "body": b"345", "more_body": False},
            ]
        )
        captured = []

        async def receive():
            return next(messages)

        async def send(message):
            pass

        async def application(scope, receive, send):
            captured.append(await receive())

        await RequestBodyLimit(application, max_bytes=5)({"type": "http"}, receive, send)
        assert captured == [{"type": "http.request", "body": b"12345", "more_body": False}]

    asyncio.run(scenario())

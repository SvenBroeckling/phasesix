import json

import redis
import redis.asyncio as aioredis
from django.conf import settings
from django.contrib.auth.models import User
from django.http import StreamingHttpResponse


def send_broadcast_sse_message(event, data):
    r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
    for user in User.objects.active():
        r.publish(
            f"eventstream.user.{user.id}",
            json.dumps({"user": user.id, "event": event, "data": data}),
        )
    r.close()


def send_session_sse_message(request, event, data):
    r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
    r.publish(
        f"eventstream.session.{request.session.session_key}",
        json.dumps(
            {"session_id": request.session.session_key, "event": event, "data": data}
        ),
    )
    r.close()


def send_user_sse_message(user: User | int, event, data):
    if isinstance(user, int):
        try:
            user = User.objects.get(id=user)
        except User.DoesNotExist:
            return

    r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
    r.publish(
        f"eventstream.user.{user.id}",
        json.dumps({"user": user.id, "event": event, "data": data}),
    )
    r.close()


async def event_stream_generator(request):
    r = aioredis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

    pubsub = r.pubsub()
    await pubsub.subscribe(f"eventstream.session.{request.session.session_key}")
    if request.user.is_authenticated:
        await pubsub.subscribe(f"eventstream.user.{request.user.id}")

    while True:
        message = await pubsub.get_message(timeout=15)
        if message and message.get("type", "") == "message":
            event_data = json.loads(message["data"].decode("utf-8"))
            yield f"event: {event_data['event']}\ndata: {json.dumps(event_data['data'])}\n\n"
        else:
            yield ":\n\n"


async def events(request):
    response = StreamingHttpResponse(
        event_stream_generator(request), status=200, content_type="text/event-stream"
    )
    response["Cache-Control"] = ("no-cache",)
    return response

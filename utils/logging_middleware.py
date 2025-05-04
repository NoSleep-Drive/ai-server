import datetime
import uuid
from starlette.concurrency import iterate_in_threadpool

from fastapi import Request, Response
from starlette.responses import StreamingResponse
from utils.helper import get_middleware_logger, set_request_uuid

middle_logger = get_middleware_logger()


async def log_request(request: Request, call_next):

    uuid_str = str(uuid.uuid4())
    set_request_uuid(uuid_str)  # helper.py의 UUID 저장소에 저장

    start_time = datetime.datetime.utcnow()

    middle_logger.info(f"Start [{uuid_str}] ---------------------")
    client_ip = request.client.host
    middle_logger.info(f"   [{uuid_str}] Client IP: {client_ip}")
    middle_logger.info(f"   [{uuid_str}] Request: {request.method} {request.url}")

    try:
        request_body = await request.body()
        middle_logger.info(f"   [{uuid_str}] Request Body: {request_body.decode(errors='ignore')}")
    except Exception as e:
        middle_logger.warning(f"   [{uuid_str}] Request Body Read Error: {e}")

    response = await call_next(request)

    middle_logger.info(f"   [{uuid_str}] Response: {response.status_code}")
    endpoint = request.scope.get("endpoint")
    endpoint_name = None
    if endpoint:
        endpoint_name = endpoint.__name__
        middle_logger.info(f"   [{uuid_str}] Processed by endpoint: {endpoint_name}")
    else:
        middle_logger.info(f"   [{uuid_str}] No endpoint info available")


    middle_logger.info(f"   [{uuid_str}] Response: {response.status_code}")
    response_body = [chunk async for chunk in response.body_iterator]
    response.body_iterator = iterate_in_threadpool(iter(response_body))
    middle_logger.info(f"   [{uuid_str}] Response Body: {response_body[0].decode()}")

    process_time = (datetime.datetime.utcnow() - start_time).total_seconds()
    middle_logger.info(f"   [{uuid_str}] Process-Time: {process_time:.3f} sec")
    middle_logger.info(f"End [{uuid_str}] -----------------------")

    return response

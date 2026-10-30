from typing import Any

from rest_framework.response import Response


def api_response(data: Any, *, api_status: int, message: str = '') -> Response:
    response = Response()
    response.data = {
        'data': data,
        'message': message,
    }
    response.status_code = api_status
    return response

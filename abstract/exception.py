import logging

from rest_framework import status
from rest_framework.views import exception_handler

from abstract.response import api_response

logger = logging.getLogger(__name__)


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        logger.error(
            'Unhandled exception in DRF API view',
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        return api_response(
            {'detail': 'Internal server error.'},
            api_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message='Internal server error.',
        )

    response.data = {
        'data': response.data,
        'message': _exception_message(response.data, response.status_code),
    }
    return response


def _exception_message(data, response_status):
    """Return a short, readable message while retaining details under data."""
    if isinstance(data, dict):
        parts = []
        for field, value in data.items():
            messages = value if isinstance(value, (list, tuple)) else [value]
            for item in messages:
                if isinstance(item, dict):
                    parts.append(f'{field}: {_exception_message(item, response_status)}')
                else:
                    parts.append(f'{field}: {item}')
        if parts:
            return '; '.join(parts)
    elif isinstance(data, (list, tuple)):
        parts = [str(item) for item in data]
        if parts:
            return '; '.join(parts)

    if response_status == status.HTTP_404_NOT_FOUND:
        return 'The requested resource was not found.'
    if response_status == status.HTTP_405_METHOD_NOT_ALLOWED:
        return 'This HTTP method is not supported for this endpoint.'
    if response_status == status.HTTP_400_BAD_REQUEST:
        return 'The request could not be processed.'
    return 'The request failed.'

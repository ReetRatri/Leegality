from collections.abc import Iterable, Mapping
from typing import Any

from rest_framework.exceptions import ValidationError


def validate_request(required_fields: Iterable[str], data: Mapping[str, Any]) -> None:
    if not isinstance(data, Mapping):
        raise ValidationError({'non_field_errors': ['Expected a JSON object.']})

    errors = {}
    for field in required_fields:
        if field not in data or data[field] is None:
            errors[field] = ['This field is required.']
        elif isinstance(data[field], str) and not data[field].strip():
            errors[field] = ['This field may not be blank.']

    if errors:
        raise ValidationError(errors)

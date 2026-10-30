import json
from collections.abc import Mapping

from rest_framework.exceptions import APIException, ValidationError
from rest_framework import status
from rest_framework.views import APIView

from abstract.function import validate_request
from abstract.response import api_response
from leegality.models import Node, RouteHistory
from leegality.service.services import find_shortest_route


class ShortestRouteView(APIView):
    @staticmethod
    def _history_value(value):
        if value is None:
            return ''
        if isinstance(value, str):
            return value[:255]
        return json.dumps(value, ensure_ascii=False, default=str)[:255]

    def _save_history(
        self, source, destination, *, latency=None, path=None, outcome, message=''
    ):
        RouteHistory.objects.create(
            source=self._history_value(source),
            destination=self._history_value(destination),
            latency=latency,
            path=path,
            status=outcome,
            message=message,
        )

    def post(self, request):
        try:
            body = request.data
        except APIException as exc:
            self._save_history(
                None,
                None,
                outcome=RouteHistory.STATUS_ERROR,
                message=json.dumps(exc.detail, ensure_ascii=False, default=str),
            )
            return api_response(
                exc.detail,
                api_status=exc.status_code,
                message='Invalid request data.',
            )

        source_value = body.get('source') if isinstance(body, Mapping) else None
        destination_value = body.get('destination') if isinstance(body, Mapping) else None

        try:
            validate_request(['source', 'destination'], body)
        except ValidationError as exc:
            error_data = exc.detail
            self._save_history(
                source_value,
                destination_value,
                outcome=RouteHistory.STATUS_ERROR,
                message=json.dumps(error_data, ensure_ascii=False, default=str),
            )
            return api_response(
                error_data,
                api_status=status.HTTP_400_BAD_REQUEST,
                message='Source and destination are required.',
            )

        source_value = body['source']
        destination_value = body['destination']
        errors = {}
        for field, value in (
            ('source', source_value),
            ('destination', destination_value),
        ):
            if isinstance(value, bool) or not isinstance(value, (int, str)):
                errors[field] = ['Must be a node name or integer node ID.']
            elif isinstance(value, int) and not 1 <= value <= 2147483647:
                errors[field] = ['Node ID must be a positive 32-bit integer.']
        if errors:
            self._save_history(
                source_value,
                destination_value,
                outcome=RouteHistory.STATUS_ERROR,
                message=json.dumps(errors, ensure_ascii=False),
            )
            return api_response(
                errors,
                api_status=status.HTTP_400_BAD_REQUEST,
                message='Source or destination has an invalid format.',
            )

        source_query = (
            Node.objects.filter(pk=source_value)
            if isinstance(source_value, int)
            else Node.objects.filter(name=source_value)
        )
        destination_query = (
            Node.objects.filter(pk=destination_value)
            if isinstance(destination_value, int)
            else Node.objects.filter(name=destination_value)
        )
        source = source_query.first()
        destination = destination_query.first()

        errors = {}
        if source is None:
            errors['source'] = [f'Node {source_value!r} was not found.']
        if destination is None:
            errors['destination'] = [f'Node {destination_value!r} was not found.']
        if errors:
            self._save_history(
                source.name if source is not None else source_value,
                destination.name if destination is not None else destination_value,
                outcome=RouteHistory.STATUS_ERROR,
                message=json.dumps(errors, ensure_ascii=False),
            )
            return api_response(
                errors,
                api_status=status.HTTP_400_BAD_REQUEST,
                message='Source or destination node was not found.',
            )

        result = find_shortest_route(source.id, destination.id)
        if result is None:
            error_message = (
                f'No path exists between {source.name} and {destination.name}'
            )
            self._save_history(
                source.name,
                destination.name,
                outcome=RouteHistory.STATUS_ERROR,
                message=error_message,
            )
            return api_response(
                {'error': error_message},
                api_status=status.HTTP_404_NOT_FOUND,
                message=error_message,
            )

        total_latency, path_ids = result
        nodes_by_id = Node.objects.in_bulk(path_ids)
        path = [nodes_by_id[node_id].name for node_id in path_ids]
        self._save_history(
            source.name,
            destination.name,
            latency=total_latency,
            path=path,
            outcome=RouteHistory.STATUS_SUCCESS,
        )
        return api_response(
            {
                'total_latency': total_latency,
                'path': path,
            },
            api_status=status.HTTP_200_OK,
            message='Shortest route found successfully.',
        )

from datetime import datetime

from rest_framework import status
from rest_framework.views import APIView

from abstract.response import api_response
from leegality.models import RouteHistory


class ShortestRouteHistoryView(APIView):
    @staticmethod
    def _parse_filter_date(field, value, errors):
        try:
            return datetime.strptime(value, '%d-%m-%Y').date()
        except ValueError:
            errors[field] = ['Use the dd-mm-yyyy format, for example 20-02-2026.']
            return None

    def get(self, request):
        errors = {}
        source = request.query_params.get('source')
        destination = request.query_params.get('destination')
        limit_value = request.query_params.get('limit')

        try:
            limit = int(limit_value) if limit_value is not None else None
            if limit is not None and limit <= 0:
                errors['limit'] = ['Must be a positive integer.']
        except ValueError:
            limit = None
            errors['limit'] = ['Must be a positive integer.']

        date_from_value = request.query_params.get('date_from')
        date_to_value = request.query_params.get('date_to')
        date_from = (
            self._parse_filter_date('date_from', date_from_value, errors)
            if date_from_value is not None
            else None
        )
        date_to = (
            self._parse_filter_date('date_to', date_to_value, errors)
            if date_to_value is not None
            else None
        )
        if date_from is not None and date_to is not None and date_from > date_to:
            errors['date_from'] = ['Must be earlier than or equal to date_to.']
        if errors:
            return api_response(
                errors,
                api_status=status.HTTP_400_BAD_REQUEST,
                message='Invalid route history filters.',
            )

        history = RouteHistory.objects.all()
        if source is not None:
            history = history.filter(source=source)
        if destination is not None:
            history = history.filter(destination=destination)
        if date_from is not None:
            history = history.filter(created_at__date__gte=date_from)
        if date_to is not None:
            history = history.filter(created_at__date__lte=date_to)
        history = history.order_by('-created_at', '-id')
        if limit is not None:
            history = history[:limit]

        data = [
            {
                'id': item.id,
                'source': item.source,
                'destination': item.destination,
                'total_latency': item.latency,
                'path': item.path,
                'status': item.status,
                'message': item.message,
                'created_at': item.created_at,
            }
            for item in history
        ]
        return api_response(
            data,
            api_status=status.HTTP_200_OK,
            message='Route history retrieved successfully.',
        )

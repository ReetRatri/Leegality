import math

from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView

from abstract.function import validate_request
from abstract.response import api_response
from leegality.models import Edge, Node


class EdgeCreateView(APIView):
    def get(self, request):
        edges = list(
            Edge.objects.select_related('source', 'destination').order_by('id')
        )
        if not edges:
            return api_response(
                [],
                api_status=status.HTTP_404_NOT_FOUND,
                message='No edges found.',
            )
        data = [
            {
                'id': edge.id,  
                'source_id': edge.source_id,
                'source': edge.source.name,
                'destination_id': edge.destination_id,
                'destination': edge.destination.name,
                'latency': edge.latency,
            }
            for edge in edges
        ]
        return api_response(
            data,
            api_status=status.HTTP_200_OK,
            message='Edges retrieved successfully.',
        )

    def post(self, request):
        try:
            validate_request(['source', 'destination', 'latency'], request.data)
        except ValidationError as exc:
            validation_messages = [
                f'{field}: {error}'
                for field, field_errors in exc.detail.items()
                for error in field_errors
            ]
            return api_response(
                {},
                api_status=status.HTTP_400_BAD_REQUEST,
                message='; '.join(validation_messages),
            )

        source_name = request.data['source']
        destination_name = request.data['destination']
        latency = request.data['latency']

        errors = []
        if not isinstance(source_name, str):
            errors.append('source must be a string.')
        if not isinstance(destination_name, str):
            errors.append('destination must be a string.')
        if (
            isinstance(latency, bool)
            or not isinstance(latency, (int, float))
            or not math.isfinite(latency)
            or latency <= 0
        ):
            errors.append('latency must be a number greater than zero.')
        if errors:
            return api_response(
                {},
                api_status=status.HTTP_400_BAD_REQUEST,
                message=' '.join(errors),
            )

        source = Node.objects.filter(name=source_name).first()
        destination = Node.objects.filter(name=destination_name).first()
        errors = []
        if source is None:
            errors.append(f'Node {source_name!r} was not found.')
        if destination is None:
            errors.append(f'Node {destination_name!r} was not found.')
        if errors:
            return api_response(
                {},
                api_status=status.HTTP_400_BAD_REQUEST,
                message=' '.join(errors),
            )

        try:
            with transaction.atomic():
                edge = Edge.objects.create(
                    source=source,
                    destination=destination,
                    latency=latency,
                )
        except IntegrityError:
            return api_response(
                {},
                api_status=status.HTTP_400_BAD_REQUEST,
                message='This edge already exists.',
            )

        return api_response(
            {
                'id': edge.id,
                'source': source.name,
                'destination': destination.name,
                'latency': edge.latency,
            },
            message='Edge created successfully.',
            api_status=status.HTTP_201_CREATED,
        )


class EdgeDeleteView(APIView):
    def delete(self, request, edge_id):
        edge = Edge.objects.select_related('source', 'destination').filter(
            pk=edge_id
        ).first()
        if edge is None:
            return api_response(
                {},
                api_status=status.HTTP_404_NOT_FOUND,
                message=f'Edge with id {edge_id} was not found.',
            )

        edge_data = {
            'id': edge.id,
            'source': edge.source.name,
            'destination': edge.destination.name,
            'latency': edge.latency,
        }
        edge.delete()
        return api_response(
            edge_data,
            api_status=status.HTTP_200_OK,
            message='Edge deleted successfully.',
        )

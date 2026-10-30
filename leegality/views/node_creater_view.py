from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.views import APIView

from abstract.function import validate_request
from abstract.response import api_response
from leegality.models import Node


class NodeCreateView(APIView):
    def post(self, request):
        validate_request(['name'], request.data)

        name = request.data['name']
        if not isinstance(name, str):
            return api_response(
                {'name': ['Must be a string.']},
                api_status=status.HTTP_400_BAD_REQUEST,
                message='Node name must be a string.',
            )

        try:
            with transaction.atomic():
                node = Node.objects.create(name=name)
        except IntegrityError:
            return api_response(
                {'name': name},
                api_status=status.HTTP_400_BAD_REQUEST,
                message=f'Node with name {name!r} already exists.',
            )

        return api_response(
            {'id': node.id, 'name': node.name},
            api_status=status.HTTP_201_CREATED,
            message='Node created successfully.',
        )

    def get(self, request):
        name = request.query_params.get('name')
        nodes = Node.objects.order_by('id')
        if name is not None:
            nodes = nodes.filter(name=name)
        nodes = list(nodes)
        if not nodes:
            return api_response(
                [],
                api_status=status.HTTP_404_NOT_FOUND,
                message='No nodes found.',
            )

        data = [{'id': node.id, 'name': node.name} for node in nodes]
        return api_response(
            data,
            api_status=status.HTTP_200_OK,
            message='Nodes retrieved successfully.',
        )


class NodeDeleteView(APIView):
    def delete(self, request, node_id):
        node = Node.objects.filter(pk=node_id).first()
        if node is None:
            return api_response(
                {},
                api_status=status.HTTP_404_NOT_FOUND,
                message=f'Node with id {node_id} was not found.',
            )

        node_data = {'id': node.id, 'name': node.name}
        node.delete()
        return api_response(
            node_data,
            api_status=status.HTTP_200_OK,
            message='Node deleted successfully.',
        )

from pathlib import Path

from django.db import connection
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .models import Edge, Node, RouteHistory


class CreateNodeTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_table_sql = Path(__file__).parent / 'sql' / 'create_node_table.sql'
        with connection.cursor() as cursor:
            cursor.execute(create_table_sql.read_text(encoding='utf-8'))

    def setUp(self):
        self.client = APIClient()

    def test_create_node_returns_id_and_name(self):
        response = self.client.post('/nodes', {'name': 'ServerA'}, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['data']['name'], 'ServerA')
        self.assertIn('id', response.data['data'])
        self.assertEqual(response.data['message'], 'Node created successfully.')
        self.assertEqual(Node.objects.count(), 1)

    def test_missing_name_is_rejected(self):
        response = self.client.post('/nodes', {}, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Node.objects.count(), 0)

    def test_empty_name_is_rejected(self):
        response = self.client.post('/nodes', {'name': ''}, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Node.objects.count(), 0)

    def test_duplicate_name_is_rejected(self):
        Node.objects.create(name='ServerA')

        response = self.client.post('/nodes', {'name': 'ServerA'}, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Node.objects.count(), 1)

    def test_non_string_name_is_rejected(self):
        response = self.client.post('/nodes', {'name': ['ServerA']}, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Node.objects.count(), 0)

    def test_get_nodes_returns_list(self):
        Node.objects.create(name='ServerA')

        response = self.client.get('/nodes')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data'], [{'id': 1, 'name': 'ServerA'}])
        self.assertEqual(response.data['message'], 'Nodes retrieved successfully.')


class CompleteApiTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        sql_directory = Path(__file__).parent / 'sql'
        with connection.cursor() as cursor:
            for filename in (
                'create_node_table.sql',
                'create_edge_table.sql',
                'create_route_history_table.sql',
            ):
                cursor.execute((sql_directory / filename).read_text(encoding='utf-8'))

    def setUp(self):
        self.client = APIClient()

    def create_node(self, name):
        return Node.objects.create(name=name)

    def test_node_validation_returns_message_in_envelope(self):
        response = self.client.post('/nodes', {}, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('name', response.data['data'])
        self.assertEqual(response.data['message'], 'name: This field is required.')

    def test_edge_create_list_and_duplicate(self):
        source = self.create_node('ServerA')
        destination = self.create_node('ServerB')
        payload = {
            'source': source.name,
            'destination': destination.name,
            'latency': 12.5,
        }

        created = self.client.post('/edges', payload, format='json')
        listed = self.client.get('/edges')
        duplicate = self.client.post('/edges', payload, format='json')

        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.data['message'], 'Edge created successfully.')
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.data['data'][0]['source_id'], source.id)
        self.assertEqual(listed.data['data'][0]['destination_id'], destination.id)
        self.assertEqual(listed.data['message'], 'Edges retrieved successfully.')
        self.assertEqual(duplicate.status_code, 400)
        self.assertEqual(duplicate.data['data'], {})
        self.assertEqual(duplicate.data['message'], 'This edge already exists.')

    def test_empty_lists_and_edge_delete_return_envelope_messages(self):
        empty_nodes = self.client.get('/nodes')
        empty_edges = self.client.get('/edges')
        source = self.create_node('ServerA')
        destination = self.create_node('ServerB')
        edge = Edge.objects.create(source=source, destination=destination, latency=2)
        deleted = self.client.delete(f'/edges/{edge.id}')

        self.assertEqual(empty_nodes.status_code, 404)
        self.assertEqual(empty_nodes.data['message'], 'No nodes found.')
        self.assertEqual(empty_edges.status_code, 404)
        self.assertEqual(empty_edges.data['message'], 'No edges found.')
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(deleted.data['message'], 'Edge deleted successfully.')

    def test_shortest_route_and_same_node_route_are_saved(self):
        source = self.create_node('ServerA')
        middle = self.create_node('ServerB')
        destination = self.create_node('ServerC')
        Edge.objects.create(source=source, destination=middle, latency=4)
        Edge.objects.create(source=middle, destination=destination, latency=6)

        response = self.client.post(
            '/routes/shortest',
            {'source': 'ServerA', 'destination': 'ServerC'},
            format='json',
        )
        same_node = self.client.post(
            '/routes/shortest',
            {'source': source.id, 'destination': source.id},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['total_latency'], 10)
        self.assertEqual(
            response.data['data']['path'],
            ['ServerA', 'ServerB', 'ServerC'],
        )
        self.assertEqual(response.data['message'], 'Shortest route found successfully.')
        self.assertEqual(same_node.status_code, 200)
        self.assertEqual(same_node.data['data']['total_latency'], 0)
        self.assertEqual(same_node.data['data']['path'], ['ServerA'])
        self.assertEqual(RouteHistory.objects.count(), 2)
        self.assertEqual(RouteHistory.objects.filter(status='success').count(), 2)

    def test_no_route_returns_message_and_saves_error_history(self):
        self.create_node('ServerA')
        self.create_node('ServerC')

        response = self.client.post(
            '/routes/shortest',
            {'source': 'ServerA', 'destination': 'ServerC'},
            format='json',
        )

        self.assertEqual(response.status_code, 404)
        self.assertIn('No path exists', response.data['message'])
        history = RouteHistory.objects.get()
        self.assertEqual(history.status, RouteHistory.STATUS_ERROR)
        self.assertEqual(history.message, response.data['message'])

    def test_history_filters_and_invalid_date_have_messages(self):
        source = self.create_node('ServerA')
        destination = self.create_node('ServerB')
        RouteHistory.objects.create(
            source=source.name,
            destination=destination.name,
            latency=3,
            path=[source.name, destination.name],
            status=RouteHistory.STATUS_SUCCESS,
            message='',
        )

        today = timezone.localdate().strftime('%d-%m-%Y')
        filtered = self.client.get(
            f'/routes/history?source=ServerA&limit=1&date_from={today}&date_to={today}'
        )
        invalid = self.client.get('/routes/history?date_from=2026-02-20')

        self.assertEqual(filtered.status_code, 200)
        self.assertEqual(len(filtered.data['data']), 1)
        self.assertEqual(
            filtered.data['message'],
            'Route history retrieved successfully.',
        )
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(invalid.data['message'], 'Invalid route history filters.')

    def test_unknown_route_node_is_rejected_and_recorded(self):
        self.create_node('ServerA')

        response = self.client.post(
            '/routes/shortest',
            {'source': 'ServerA', 'destination': 'MissingServer'},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['message'],
            'Source or destination node was not found.',
        )
        history = RouteHistory.objects.get()
        self.assertEqual(history.status, RouteHistory.STATUS_ERROR)

    def test_delete_node_cascades_edges_and_delete_edge_reports_missing(self):
        source = self.create_node('ServerA')
        destination = self.create_node('ServerB')
        edge = Edge.objects.create(source=source, destination=destination, latency=2)

        deleted_node = self.client.delete(f'/nodes/{source.id}')
        deleted_edge = self.client.delete(f'/edges/{edge.id}')

        self.assertEqual(deleted_node.status_code, 200)
        self.assertEqual(deleted_node.data['message'], 'Node deleted successfully.')
        self.assertEqual(Edge.objects.count(), 0)
        self.assertEqual(deleted_edge.status_code, 404)
        self.assertEqual(
            deleted_edge.data['message'],
            f'Edge with id {edge.id} was not found.',
        )

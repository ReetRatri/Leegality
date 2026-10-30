import heapq
from collections import defaultdict

from leegality.models import Edge


def find_shortest_route(source_id: int, destination_id: int):
    """Return (total latency, path node IDs), or None when no path exists."""
    adjacency = defaultdict(list)
    edges = Edge.objects.order_by('source_id', 'destination_id', 'id').values_list(
        'source_id', 'destination_id', 'latency'
    )
    for edge_source_id, edge_destination_id, latency in edges:
        adjacency[edge_source_id].append((edge_destination_id, latency))

    distances = {source_id: 0.0}
    previous = {}
    queue = [(0.0, source_id)]

    while queue:
        current_latency, current_id = heapq.heappop(queue)
        if current_latency > distances.get(current_id, float('inf')):
            continue
        if current_id == destination_id:
            break

        for next_id, edge_latency in adjacency[current_id]:
            candidate_latency = current_latency + edge_latency
            if candidate_latency < distances.get(next_id, float('inf')):
                distances[next_id] = candidate_latency
                previous[next_id] = current_id
                heapq.heappush(queue, (candidate_latency, next_id))

    if destination_id not in distances:
        return None

    path = [destination_id]
    while path[-1] != source_id:
        path.append(previous[path[-1]])
    path.reverse()
    return distances[destination_id], path

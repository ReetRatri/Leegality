# Leegality Network Route API

Base URL: `http://127.0.0.1:8000`

The API currently does not require an API token. Responses use this envelope:

```json
{
  "data": {},
  "message": "A short result or error description."
}
```

Successful responses include a success message. Error responses keep structured details in `data` and provide a readable message in `message`.

## Nodes

### `POST /nodes`

Create a node.

Request:

```json
{
  "name": "ServerA"
}
```

Success: `201 Created`

```json
{
  "data": {
    "id": 1,
    "name": "ServerA"
  },
  "message": "Node created successfully."
}
```

Returns `400 Bad Request` if the name is missing or already exists.

For a duplicate name, the response identifies the name and explains the error:

```json
{
  "data": {
    "name": "ServerA"
  },
  "message": "Node with name 'ServerA' already exists."
}
```

### `DELETE /nodes/{id}`

Delete a node by its ID. Deleting a node also deletes its connected edges. Route history is retained.

Example: `DELETE /nodes/1`

Success: `200 OK`

```json
{
  "data": {
    "id": 1,
    "name": "ServerA"
  },
  "message": "Node deleted successfully."
}
```

Returns `404 Not Found` if the node ID does not exist.

### `GET /nodes`

List nodes. Optional query parameter: `name`.

Example: `GET /nodes?name=ServerA`

Success: `200 OK`

```json
{
  "data": [
    {
      "id": 1,
      "name": "ServerA"
    }
  ],
  "message": "Nodes retrieved successfully."
}
```

If no nodes match (including a `name` filter), the endpoint returns `404 Not Found` with an empty `data` list and `message: "No nodes found."`.

## Edges

Edges are directed from `source` to `destination`.

### `POST /edges`

Create an edge between existing nodes. This endpoint accepts node names.

Request:

```json
{
  "source": "ServerA",
  "destination": "ServerB",
  "latency": 12.5
}
```

Success: `201 Created`

```json
{
  "data": {
    "id": 1,
    "source": "ServerA",
    "destination": "ServerB",
    "latency": 12.5
  },
  "message": "Edge created successfully."
}
```

Returns `400 Bad Request` if required fields are missing, either node does not exist, latency is not greater than zero, or the directed edge already exists. Error details are returned in `message`, with `data` set to `{}`. For example:

```json
{
  "data": {},
  "message": "source: This field is required."
}
```

### `DELETE /edges/{id}`

Delete an edge by its ID.

Example: `DELETE /edges/1`

Success: `200 OK`

```json
{
  "data": {
    "id": 1,
    "source": "ServerA",
    "destination": "ServerB",
    "latency": 12.5
  },
  "message": "Edge deleted successfully."
}
```

Returns `404 Not Found` if the edge ID does not exist.

### `GET /edges`

List edges, including edge and endpoint node IDs.

Success: `200 OK`

```json
{
  "data": [
    {
      "id": 1,
      "source_id": 1,
      "source": "ServerA",
      "destination_id": 2,
      "destination": "ServerB",
      "latency": 12.5
    }
  ],
  "message": "Edges retrieved successfully."
}
```

## Shortest route

### `POST /routes/shortest`

Find the route with the lowest total latency. `source` and `destination` may be node names (strings) or node IDs (integers). Edges are followed in their stored direction.

Request using names:

```json
{
  "source": "ServerA",
  "destination": "ServerB"
}
```

Request using IDs:

```json
{
  "source": 1,
  "destination": 2
}
```

Success: `200 OK`

```json
{
  "data": {
    "total_latency": 12.5,
    "path": ["ServerA", "ServerB"]
  },
  "message": "Shortest route found successfully."
}
```

If source and destination resolve to the same node, the API returns latency `0` and a path containing that node once. Returns `400 Bad Request` for missing, invalid, or unknown nodes. Returns `404 Not Found` if no route exists.

No-route response:

```json
{
  "data": {
    "error": "No path exists between ServerA and ServerB"
  },
  "message": "No path exists between ServerA and ServerB"
}
```

## Route history

### `GET /routes/history`

List route queries newest first. All query parameters are optional:

| Parameter | Description |
| --- | --- |
| `source` | Filter by stored source node name |
| `destination` | Filter by stored destination node name |
| `limit` | Maximum number of results; must be a positive integer |
| `date_from` | Include records on or after this date |
| `date_to` | Include records on or before this date |

Dates use `dd-mm-yyyy`. The `date_to` filter includes the full day.

Example:

```text
GET /routes/history?source=ServerA&limit=10&date_from=20-02-2026&date_to=28-02-2026
```

Success: `200 OK`

```json
{
  "data": [
    {
      "id": 1,
      "source": "ServerA",
      "destination": "ServerB",
      "total_latency": 12.5,
      "path": ["ServerA", "ServerB"],
      "status": "success",
      "message": "",
      "created_at": "2026-02-20T14:32:00Z"
    }
  ],
  "message": "Route history retrieved successfully."
}
```

Error history entries have `status: "error"`, a `null` latency and path, and the error details in their item-level `message`. The envelope message confirms that the history query completed.

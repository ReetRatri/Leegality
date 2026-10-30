# Leegality Network Route API

A Django REST Framework API for creating nodes and directed edges, finding shortest routes, and reviewing route history.

See [api-doc.md](api-doc.md) for the endpoint documentation. Import [leegality.postman_collection.json](leegality.postman_collection.json) into Postman to try the requests.

## Setup

Use Python 3.12 or newer. From the project directory, run these commands in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py shell -c 'from pathlib import Path; from django.db import connection; connection.cursor().execute(Path("leegality/sql/create_node_table.sql").read_text())'
python manage.py shell -c 'from pathlib import Path; from django.db import connection; connection.cursor().execute(Path("leegality/sql/create_edge_table.sql").read_text())'
python manage.py shell -c 'from pathlib import Path; from django.db import connection; connection.cursor().execute(Path("leegality/sql/create_route_history_table.sql").read_text())'
python -m uvicorn config.asgi:application --reload
```

For deployment, set `DJANGO_SECRET_KEY` to a private random value, set `DJANGO_DEBUG=false`, and set `DJANGO_ALLOWED_HOSTS` to a comma-separated list of allowed hostnames. The built-in key and host defaults are for local development only.

The migration command sets up Django's built-in tables. The SQL commands create the app's `node_creater`, `edge_creater`, and `route_history` tables manually. If you created the original `route_history` table before status tracking, upgrade it with:

```powershell
python manage.py shell -c "from pathlib import Path; from django.db import connection; connection.ensure_connection(); connection.connection.executescript(Path('leegality/sql/upgrade_route_history_table.sql').read_text())"
```

The history table stores each shortest-route request with `success` or `error` status and the displayed error details in `message`. Failed requests have a null latency. Uvicorn serves the Django ASGI application at `http://127.0.0.1:8000`. The project uses SQLite by default.

If you already applied the status-tracking upgrade, add the path column once with:

```powershell
python manage.py shell -c "from pathlib import Path; from django.db import connection; connection.cursor().execute(Path('leegality/sql/add_route_history_path.sql').read_text())"
```

## Create a node

Send a JSON request to `POST /nodes`:

```json
{
  "name": "ServerA"
}
```

A successful request returns `201 Created` in the standard envelope:

```json
{
  "data": {"id": 1, "name": "ServerA"},
  "message": "Node created successfully."
}
```

`GET /nodes` returns all nodes, including their IDs, in the same envelope:

```json
{
  "data": [
    {"id": 1, "name": "ServerA"},
    {"id": 2, "name": "ServerB"}
  ],
  "message": "Nodes retrieved successfully."
}
```

If there are no nodes, or no node matches the optional `name` filter, it returns `404 Not Found` with `data: []` and `message: "No nodes found."`.

## Create an edge

Create a directed edge between two existing nodes with `POST /edges`:

```json
{
  "source": "ServerA",
  "destination": "ServerB",
  "latency": 12.5
}
```

A successful request returns `201 Created`:

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

The endpoint returns `400 Bad Request` if either node is missing, the latency is not greater than zero, or that directed edge already exists.

`GET /edges` lists existing edges with their own IDs and both endpoint node IDs and names. This lets you inspect the graph and map node names to IDs:

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

## Get the shortest route

Send `POST /routes/shortest` with node names or integer IDs. For example, names:

```json
{
  "source": "ServerA",
  "destination": "ServerD"
}
```

Or IDs returned by `GET /nodes`:

```json
{
  "source": 1,
  "destination": 4
}
```

When a route exists, the API returns its total latency and node names in the path:

```json
{
  "data": {
    "total_latency": 23.4,
    "path": ["ServerA", "ServerB", "ServerD"]
  },
  "message": "Shortest route found successfully."
}
```

The search follows directed edges. If source and destination resolve to the same node, the API returns latency `0` and a path containing that node once. A missing route returns `404`; missing, invalid, or unknown nodes return `400`.

If no route exists, the response is:

```json
{
  "data": {"error": "No path exists between ServerA and ServerD"},
  "message": "No path exists between ServerA and ServerD"
}
```

## Get route history

`GET /routes/history` returns route queries newest first. Optional query parameters are `source`, `destination`, `limit`, `date_from`, and `date_to`. Source and destination filters match the stored node names; date filters use `dd-mm-yyyy` (for example, `20-02-2026`). The `date_to` date includes the full day.

```text
GET /routes/history?source=ServerA&limit=10&date_from=20-02-2026
```

Each history item includes the route result and its status. Error rows have `null` latency and path, with the displayed error details in the item's `message`. The response envelope has the message `Route history retrieved successfully.`

Run the API checks with:

```powershell
python manage.py test leegality
```

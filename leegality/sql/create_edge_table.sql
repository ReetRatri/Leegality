CREATE TABLE IF NOT EXISTS edge_creater (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL REFERENCES node_creater(id) ON DELETE CASCADE,
    destination_id INTEGER NOT NULL REFERENCES node_creater(id) ON DELETE CASCADE,
    latency REAL NOT NULL CHECK (latency > 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (source_id, destination_id)
);

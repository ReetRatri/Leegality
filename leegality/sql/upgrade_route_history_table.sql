BEGIN TRANSACTION;

ALTER TABLE route_history RENAME TO route_history_old;

CREATE TABLE route_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source VARCHAR(255) NOT NULL,
    destination VARCHAR(255) NOT NULL,
    latency REAL CHECK (latency >= 0),
    path JSON,
    status VARCHAR(7) NOT NULL CHECK (status IN ('success', 'error')),
    message TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO route_history (id, source, destination, latency, path, status, message, created_at)
SELECT id, source, destination, latency, NULL, 'success', '', created_at
FROM route_history_old;

DROP TABLE route_history_old;

COMMIT;

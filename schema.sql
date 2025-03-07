
CREATE TABLE IF NOT EXISTS chats (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    user_input TEXT NOT NULL,
    response TEXT NOT NULL,
    search_performed INTEGER NOT NULL,
    test_mode INTEGER NOT NULL
);

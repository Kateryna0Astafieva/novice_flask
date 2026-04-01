
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT NOT NULL,
    password TEXT NOT NULL,
    viewed_topics TEXT,
    test_results TEXT,
    liked_topics TEXT,
       name TEXT, 
        surname TEXT,
       gender TEXT,
    unique_id TEXT NOT NULL,
    remember_token TEXT
);


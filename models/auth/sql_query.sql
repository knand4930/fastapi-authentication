CREATE TABLE teammanagements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), -- or uuid_generate_v4() depending on your PostgreSQL extension
    name VARCHAR NOT NULL UNIQUE,
    user_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

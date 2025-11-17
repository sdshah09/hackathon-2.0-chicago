CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(128) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS files (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(10) NOT NULL, -- 'jpeg', 'png', 'pdf'
    file_size BIGINT NOT NULL,
    s3_bucket VARCHAR(255),
    s3_key VARCHAR(512),
    s3_url TEXT,
    upload_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'uploading', 'completed', 'failed'
    extraction_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_files_patient_id ON files(patient_id);
CREATE INDEX IF NOT EXISTS idx_files_upload_status ON files(upload_status);


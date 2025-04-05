-- Initialize PostgreSQL database for PRAGI
-- This script sets up the complete database structure including extensions, tables, and indexes

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Drop existing tables if they exist
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS upload_history CASCADE;

-- Create users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    google_id VARCHAR(255) UNIQUE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Create sessions table
CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    data JSONB,
    CONSTRAINT valid_session_id CHECK (session_id ~ '^[a-zA-Z0-9_-]+$')
);

-- Create documents table with vector support
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    encrypted_content TEXT,
    embedding vector(384),  -- Dimension matches the sentence-transformer model
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    source_type VARCHAR(50),
    processing_status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    CONSTRAINT valid_content CHECK (length(content) > 0)
);

-- Create upload history table
CREATE TABLE upload_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    filename VARCHAR(255) NOT NULL,
    file_size BIGINT,
    mime_type VARCHAR(100),
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processing_status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    metadata JSONB,
    document_ids INTEGER[] -- Array of document IDs created from this upload
);

-- Create indexes for efficient querying

-- Users indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_google_id ON users(google_id);

-- Sessions indexes
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX idx_sessions_session_id ON sessions(session_id);

-- Documents indexes
CREATE INDEX documents_embedding_idx ON documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_created_at ON documents(created_at);
CREATE INDEX idx_documents_processing_status ON documents(processing_status);
CREATE INDEX documents_metadata_idx ON documents USING GIN (metadata jsonb_path_ops);
CREATE INDEX documents_content_idx ON documents USING GIN (to_tsvector('english', content));

-- Upload history indexes
CREATE INDEX idx_upload_history_user_id ON upload_history(user_id);
CREATE INDEX idx_upload_history_upload_date ON upload_history(upload_date);
CREATE INDEX idx_upload_history_processing_status ON upload_history(processing_status);
CREATE INDEX idx_upload_history_metadata ON upload_history USING GIN (metadata jsonb_path_ops);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add helpful comments to tables
COMMENT ON TABLE documents IS 'Stores document content, embeddings, and metadata for vector similarity search';
COMMENT ON TABLE users IS 'Stores user information and authentication details';
COMMENT ON TABLE sessions IS 'Stores user session information';
COMMENT ON TABLE upload_history IS 'Tracks document upload history and processing status';

-- Grant appropriate permissions (adjust as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user; 
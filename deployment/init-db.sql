-- Intel AI Assistant Database Initialization Script
-- PostgreSQL schema for conversation storage and user management

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create database schema
CREATE SCHEMA IF NOT EXISTS intel_ai;

-- Set search path
SET search_path TO intel_ai, public;

-- Users table for authentication and preferences
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    intel_profile VARCHAR(50) DEFAULT 'auto',
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true
);

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500),
    intel_profile VARCHAR(50),
    model_used VARCHAR(100),
    status VARCHAR(20) DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    tokens_used INTEGER,
    processing_time_ms INTEGER,
    intel_device_used VARCHAR(20),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Model performance metrics
CREATE TABLE IF NOT EXISTS model_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(100) NOT NULL,
    intel_profile VARCHAR(50) NOT NULL,
    device_used VARCHAR(20) NOT NULL,
    tokens_per_second DECIMAL(10,2),
    memory_usage_mb INTEGER,
    gpu_utilization DECIMAL(5,2),
    npu_utilization DECIMAL(5,2),
    temperature DECIMAL(3,2),
    max_tokens INTEGER,
    processing_time_ms INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- System events log
CREATE TABLE IF NOT EXISTS system_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'info',
    message TEXT NOT NULL,
    details JSONB DEFAULT '{}',
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    intel_profile VARCHAR(50),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Intel hardware profiles
CREATE TABLE IF NOT EXISTS intel_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    description TEXT,
    processor_type VARCHAR(50),
    gpu_type VARCHAR(50),
    npu_type VARCHAR(50),
    capabilities JSONB NOT NULL DEFAULT '{}',
    model_configurations JSONB NOT NULL DEFAULT '{}',
    performance_presets JSONB NOT NULL DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- API keys for external services
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_name VARCHAR(100) NOT NULL,
    key_name VARCHAR(100),
    encrypted_key TEXT NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(service_name, key_name, user_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_intel_profile ON conversations(intel_profile);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role);

CREATE INDEX IF NOT EXISTS idx_model_metrics_model_name ON model_metrics(model_name);
CREATE INDEX IF NOT EXISTS idx_model_metrics_intel_profile ON model_metrics(intel_profile);
CREATE INDEX IF NOT EXISTS idx_model_metrics_timestamp ON model_metrics(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_system_events_event_type ON system_events(event_type);
CREATE INDEX IF NOT EXISTS idx_system_events_timestamp ON system_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_system_events_severity ON system_events(severity);

CREATE INDEX IF NOT EXISTS idx_intel_profiles_name ON intel_profiles(name);
CREATE INDEX IF NOT EXISTS idx_intel_profiles_active ON intel_profiles(is_active);

-- Full-text search indexes
CREATE INDEX IF NOT EXISTS idx_messages_content_fts ON messages USING gin(to_tsvector('english', content));
CREATE INDEX IF NOT EXISTS idx_conversations_title_fts ON conversations USING gin(to_tsvector('english', title));

-- Triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_intel_profiles_updated_at BEFORE UPDATE ON intel_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default Intel profiles
INSERT INTO intel_profiles (name, display_name, description, processor_type, gpu_type, npu_type, capabilities) VALUES
(
    'ultra7_arc770_npu',
    'Intel Core Ultra 7 + Arc A770 + NPU',
    'High-performance setup with Arc GPU and AI Boost NPU',
    'core_ultra_7',
    'arc_a770',
    'ai_boost_npu',
    '{"cpu": {"available": true, "cores": 16, "performance": "ultra"}, "gpu": {"available": true, "memory_mb": 16384, "performance": "ultra"}, "npu": {"available": true, "performance": "high"}}'
),
(
    'ultra7_arc750_npu',
    'Intel Core Ultra 7 + Arc A750 + NPU',
    'Mid-high performance with Arc A750 GPU and AI Boost NPU',
    'core_ultra_7',
    'arc_a750',
    'ai_boost_npu',
    '{"cpu": {"available": true, "cores": 16, "performance": "ultra"}, "gpu": {"available": true, "memory_mb": 8192, "performance": "high"}, "npu": {"available": true, "performance": "high"}}'
),
(
    'i7_irisxe',
    'Intel Core i7 + Iris Xe Graphics',
    'Mid-range setup with integrated Iris Xe graphics',
    'core_i7',
    'iris_xe',
    'none',
    '{"cpu": {"available": true, "cores": 12, "performance": "high"}, "gpu": {"available": true, "memory_mb": 4096, "performance": "medium"}, "npu": {"available": false}}'
),
(
    'i5_uhd',
    'Intel Core i5 + UHD Graphics',
    'Entry-level setup with integrated UHD graphics',
    'core_i5',
    'uhd_graphics',
    'none',
    '{"cpu": {"available": true, "cores": 8, "performance": "medium"}, "gpu": {"available": true, "memory_mb": 2048, "performance": "low"}, "npu": {"available": false}}'
),
(
    'cpu_only',
    'Intel CPU Only',
    'CPU-only configuration for systems without dedicated GPU/NPU',
    'core_i7',
    'none',
    'none',
    '{"cpu": {"available": true, "cores": 8, "performance": "medium"}, "gpu": {"available": false}, "npu": {"available": false}}'
) ON CONFLICT (name) DO NOTHING;

-- Create default admin user
INSERT INTO users (username, email, password_hash, full_name, intel_profile) VALUES
(
    'admin',
    'admin@localhost',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeZIg7m7VcMOjHJ1K', -- password: admin123
    'System Administrator',
    'auto'
) ON CONFLICT (username) DO NOTHING;

-- Grant permissions
GRANT USAGE ON SCHEMA intel_ai TO ai_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA intel_ai TO ai_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA intel_ai TO ai_user;

-- Create functions for common operations
CREATE OR REPLACE FUNCTION get_conversation_summary(conv_id UUID)
RETURNS TABLE(
    conversation_id UUID,
    title VARCHAR(500),
    message_count BIGINT,
    total_tokens INTEGER,
    avg_processing_time DECIMAL,
    intel_profile VARCHAR(50),
    model_used VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id,
        c.title,
        COUNT(m.id),
        COALESCE(SUM(m.tokens_used), 0)::INTEGER,
        COALESCE(AVG(m.processing_time_ms), 0)::DECIMAL,
        c.intel_profile,
        c.model_used,
        c.created_at,
        c.updated_at
    FROM conversations c
    LEFT JOIN messages m ON c.id = m.conversation_id
    WHERE c.id = conv_id
    GROUP BY c.id, c.title, c.intel_profile, c.model_used, c.created_at, c.updated_at;
END;
$$ LANGUAGE plpgsql;

-- Create function for performance analytics
CREATE OR REPLACE FUNCTION get_performance_analytics(
    profile_name VARCHAR(50) DEFAULT NULL,
    start_date TIMESTAMP WITH TIME ZONE DEFAULT NOW() - INTERVAL '24 hours',
    end_date TIMESTAMP WITH TIME ZONE DEFAULT NOW()
)
RETURNS TABLE(
    intel_profile VARCHAR(50),
    model_name VARCHAR(100),
    device_used VARCHAR(20),
    avg_tokens_per_second DECIMAL,
    avg_memory_usage_mb DECIMAL,
    avg_gpu_utilization DECIMAL,
    avg_npu_utilization DECIMAL,
    total_requests BIGINT,
    avg_processing_time_ms DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        mm.intel_profile,
        mm.model_name,
        mm.device_used,
        AVG(mm.tokens_per_second)::DECIMAL,
        AVG(mm.memory_usage_mb)::DECIMAL,
        AVG(mm.gpu_utilization)::DECIMAL,
        AVG(mm.npu_utilization)::DECIMAL,
        COUNT(*)::BIGINT,
        AVG(mm.processing_time_ms)::DECIMAL
    FROM model_metrics mm
    WHERE mm.timestamp BETWEEN start_date AND end_date
        AND (profile_name IS NULL OR mm.intel_profile = profile_name)
    GROUP BY mm.intel_profile, mm.model_name, mm.device_used
    ORDER BY mm.intel_profile, mm.model_name;
END;
$$ LANGUAGE plpgsql;
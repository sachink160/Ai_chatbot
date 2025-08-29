-- Initialize Subscription Tables
-- Run this script to create the necessary tables for the subscription system

-- Create subscription_plans table
CREATE TABLE IF NOT EXISTS subscription_plans (
    id VARCHAR PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    duration_days INTEGER NOT NULL,
    max_chats_per_month INTEGER NOT NULL,
    max_documents INTEGER NOT NULL,
    max_hr_documents INTEGER NOT NULL,
    max_video_uploads INTEGER NOT NULL,
    features TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create user_subscriptions table
CREATE TABLE IF NOT EXISTS user_subscriptions (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    plan_id VARCHAR NOT NULL,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    status VARCHAR DEFAULT 'active',
    payment_status VARCHAR DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (plan_id) REFERENCES subscription_plans(id) ON DELETE CASCADE
);

-- Create usage_tracking table
CREATE TABLE IF NOT EXISTS usage_tracking (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    month_year VARCHAR NOT NULL,
    chats_used INTEGER DEFAULT 0,
    documents_uploaded INTEGER DEFAULT 0,
    hr_documents_uploaded INTEGER DEFAULT 0,
    video_uploads INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Add subscription columns to users table if they don't exist
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_subscribed BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_end_date TIMESTAMP;

-- Insert default subscription plans
INSERT INTO subscription_plans (id, name, price, duration_days, max_chats_per_month, max_documents, max_hr_documents, max_video_uploads, features) VALUES
(
    gen_random_uuid()::text,
    'Basic',
    9.99,
    30,
    100,
    20,
    20,
    10,
    '["100 AI chats per month", "20 document uploads", "20 HR document uploads", "10 video uploads", "Priority support"]'
),
(
    gen_random_uuid()::text,
    'Pro',
    19.99,
    30,
    500,
    100,
    100,
    50,
    '["500 AI chats per month", "100 document uploads", "100 HR document uploads", "50 video uploads", "Advanced analytics", "Priority support", "Custom integrations"]'
),
(
    gen_random_uuid()::text,
    'Enterprise',
    49.99,
    30,
    2000,
    500,
    500,
    200,
    '["2000 AI chats per month", "500 document uploads", "500 HR document uploads", "200 video uploads", "Advanced analytics", "Priority support", "Custom integrations", "Dedicated account manager", "API access"]'
)
ON CONFLICT (name) DO NOTHING;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_plan_id ON user_subscriptions(plan_id);
CREATE INDEX IF NOT EXISTS idx_usage_tracking_user_id ON usage_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_tracking_month_year ON usage_tracking(month_year);
CREATE INDEX IF NOT EXISTS idx_subscription_plans_active ON subscription_plans(is_active);

-- Create unique constraint for usage tracking per user per month
CREATE UNIQUE INDEX IF NOT EXISTS idx_usage_tracking_user_month ON usage_tracking(user_id, month_year);

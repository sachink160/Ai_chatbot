-- Add dynamic prompt document limits to subscription plans (if not exists)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'subscription_plans' 
                   AND column_name = 'max_dynamic_prompt_documents') THEN
        ALTER TABLE subscription_plans ADD COLUMN max_dynamic_prompt_documents INTEGER DEFAULT 5;
    END IF;
END $$;

-- Add dynamic prompt document usage tracking (if not exists)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'usage_tracking' 
                   AND column_name = 'dynamic_prompt_documents_uploaded') THEN
        ALTER TABLE usage_tracking ADD COLUMN dynamic_prompt_documents_uploaded INTEGER DEFAULT 0;
    END IF;
END $$;

-- Update existing subscription plans with dynamic prompt document limits
UPDATE subscription_plans SET max_dynamic_prompt_documents = 10 WHERE name = 'Basic';
UPDATE subscription_plans SET max_dynamic_prompt_documents = 50 WHERE name = 'Pro';
UPDATE subscription_plans SET max_dynamic_prompt_documents = 200 WHERE name = 'Enterprise';

-- Update features JSON for existing plans
UPDATE subscription_plans SET features = jsonb_set(
    features::jsonb, 
    '{4}', 
    '"10 dynamic prompt document uploads"'::jsonb
) WHERE name = 'Basic';

UPDATE subscription_plans SET features = jsonb_set(
    features::jsonb, 
    '{4}', 
    '"50 dynamic prompt document uploads"'::jsonb
) WHERE name = 'Pro';

UPDATE subscription_plans SET features = jsonb_set(
    features::jsonb, 
    '{4}', 
    '"200 dynamic prompt document uploads"'::jsonb
) WHERE name = 'Enterprise';

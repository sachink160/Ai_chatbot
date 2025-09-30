-- Add GPT model column to dynamic_prompts table (if not exists)
-- This migration adds the gpt_model column with a default value

DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'dynamic_prompts' 
                   AND column_name = 'gpt_model') THEN
        ALTER TABLE dynamic_prompts ADD COLUMN gpt_model VARCHAR(50) DEFAULT 'gpt-4o-mini';
        
        -- Update existing records to have the default model
        UPDATE dynamic_prompts 
        SET gpt_model = 'gpt-4o-mini' 
        WHERE gpt_model IS NULL;
        
        -- Make the column NOT NULL after setting default values
        ALTER TABLE dynamic_prompts ALTER COLUMN gpt_model SET NOT NULL;
        
        -- Add a comment to the column
        COMMENT ON COLUMN dynamic_prompts.gpt_model IS 'GPT model to use for processing documents with this prompt';
    END IF;
END $$;

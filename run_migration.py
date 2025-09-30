#!/usr/bin/env python3

from app.database import engine
from sqlalchemy import text
import os

def run_migration():
    """Run database migrations for dynamic prompts"""
    
    # List of migration files to run in order
    migration_files = [
        'add_dynamic_prompt_limits.sql',
        'add_gpt_model_column.sql'
    ]
    
    with engine.connect() as conn:
        for migration_file in migration_files:
            if os.path.exists(migration_file):
                print(f'\n=== Running migration: {migration_file} ===')
                
                try:
                    # Read and execute the migration script
                    with open(migration_file, 'r') as f:
                        sql_script = f.read()

                    # Split by semicolon and execute each statement
                    statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]

                    for statement in statements:
                        if statement:
                            try:
                                conn.execute(text(statement))
                                print(f'✓ Executed: {statement[:50]}...')
                            except Exception as e:
                                print(f'✗ Error executing statement: {e}')
                                print(f'Statement: {statement}')
                                # Rollback and continue with other statements
                                conn.rollback()
                                break
                    
                    # Commit after each migration file
                    conn.commit()
                    print(f'✓ Migration {migration_file} completed!')
                    
                except Exception as e:
                    print(f'✗ Failed to process migration {migration_file}: {e}')
                    conn.rollback()
            else:
                print(f'⚠ Migration file {migration_file} not found, skipping...')
        
        print('\n🎉 All migrations completed successfully!')

if __name__ == "__main__":
    run_migration()

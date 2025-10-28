#!/usr/bin/env python3
"""
Alembic helper script for managing database migrations.

This script provides convenient commands for common Alembic tasks.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


def check_database_url():
    """Check if DATABASE_URL is set."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ ERROR: DATABASE_URL environment variable is not set")
        print("\nPlease set it:")
        print("  Linux/Mac: export DATABASE_URL='postgresql://user:password@localhost/dbname'")
        print("  Windows:   set DATABASE_URL=postgresql://user:password@localhost/dbname")
        return False
    
    # Mask password in output
    masked_url = db_url.split("@")[-1] if "@" in db_url else "configured"
    print(f"✅ Using database: {masked_url}")
    return True


def run_alembic_command(command):
    """Run an Alembic command."""
    if not check_database_url():
        sys.exit(1)
    
    try:
        result = subprocess.run(
            ["alembic"] + command,
            cwd=PROJECT_ROOT,
            check=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running alembic command: {e}")
        return False
    except FileNotFoundError:
        print("❌ ERROR: Alembic not found. Install it with:")
        print("  pip install alembic")
        return False


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("""
Alembic Helper Script

Usage:
  python alembic_helpers.py <command> [options]

Commands:
  status       - Show current migration status
  current      - Show current database revision
  history      - Show migration history
  heads        - Show all head revisions
  
  create NAME  - Create a new migration (manual)
  autogenerate "MESSAGE" - Create an auto-generated migration
  
  upgrade      - Apply all pending migrations
  upgrade +1   - Apply next migration only
  downgrade    - Rollback last migration
  downgrade -1 - Rollback one migration
  downgrade base - Rollback all migrations
  
  stamp <rev>  - Stamp database to a specific revision
  
Examples:
  python alembic_helpers.py status
  python alembic_helpers.py autogenerate "add user profile"
  python alembic_helpers.py upgrade
  python alembic_helpers.py downgrade -1
        """)
        sys.exit(0)
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    # Map commands to alembic commands
    command_map = {
        "status": ["current", "-v"],
        "current": ["current"],
        "history": ["history"],
        "heads": ["heads"],
        "create": ["revision", "-m"],
        "autogenerate": ["revision", "--autogenerate", "-m"],
        "upgrade": ["upgrade"] if not args else ["upgrade"] + args,
        "downgrade": ["downgrade"] if not args else ["downgrade"] + args,
        "stamp": ["stamp"],
    }
    
    if command in ["create", "autogenerate"]:
        if not args:
            print(f"❌ ERROR: {command} requires a message")
            print(f"Usage: python alembic_helpers.py {command} \"your message\"")
            sys.exit(1)
        alembic_cmd = command_map[command] + [args[0]]
    elif command == "upgrade" or command == "downgrade":
        alembic_cmd = command_map.get(command, [command]) + args
    elif command == "stamp":
        if not args:
            print("❌ ERROR: stamp requires a revision")
            print("Usage: python alembic_helpers.py stamp <revision>")
            sys.exit(1)
        alembic_cmd = ["stamp"] + args
    else:
        alembic_cmd = command_map.get(command, [command])
    
    # Run the command
    if alembic_cmd:
        success = run_alembic_command(alembic_cmd)
        sys.exit(0 if success else 1)
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()


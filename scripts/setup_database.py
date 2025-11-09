#!/usr/bin/env python3
"""
Database setup script for XCoin Scalping Bot.

This script:
1. Creates the PostgreSQL database (if it doesn't exist)
2. Runs the schema.sql file to create all tables
3. Verifies the setup

Usage:
    python scripts/setup_database.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg
from backend.config import Config


async def create_database_if_not_exists():
    """Create the database if it doesn't exist."""
    # Parse connection string to get database name
    conn_parts = Config.DATABASE_URL.split('/')
    db_name = conn_parts[-1]
    base_url = '/'.join(conn_parts[:-1])

    print(f"Checking if database '{db_name}' exists...")

    try:
        # Connect to postgres database (default)
        conn = await asyncpg.connect(f"{base_url}/postgres")

        # Check if our database exists
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            db_name
        )

        if exists:
            print(f"✓ Database '{db_name}' already exists")
        else:
            print(f"Creating database '{db_name}'...")
            # CREATE DATABASE cannot run in a transaction
            await conn.execute(f'CREATE DATABASE {db_name}')
            print(f"✓ Database '{db_name}' created")

        await conn.close()

    except Exception as e:
        print(f"✗ Error creating database: {e}")
        print("\nMake sure PostgreSQL is running and credentials are correct.")
        print(f"Connection string: {base_url}/...")
        sys.exit(1)


async def run_schema():
    """Run the schema.sql file."""
    schema_file = Path(__file__).parent.parent / 'backend' / 'database' / 'schema.sql'

    if not schema_file.exists():
        print(f"✗ Schema file not found: {schema_file}")
        sys.exit(1)

    print(f"\nRunning schema from: {schema_file}")

    # Read schema file
    with open(schema_file, 'r') as f:
        schema_sql = f.read()

    try:
        # Connect to our database
        conn = await asyncpg.connect(Config.DATABASE_URL)

        print("Executing schema SQL...")
        await conn.execute(schema_sql)

        print("✓ Schema executed successfully")

        # Verify tables were created
        tables = await conn.fetch("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)

        print(f"\n✓ Created {len(tables)} tables:")
        for table in tables:
            print(f"  - {table['tablename']}")

        # Verify views
        views = await conn.fetch("""
            SELECT viewname FROM pg_views
            WHERE schemaname = 'public'
            ORDER BY viewname
        """)

        if views:
            print(f"\n✓ Created {len(views)} views:")
            for view in views:
                print(f"  - {view['viewname']}")

        # Verify functions
        functions = await conn.fetch("""
            SELECT proname FROM pg_proc
            WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
            AND prokind = 'f'
            ORDER BY proname
        """)

        if functions:
            print(f"\n✓ Created {len(functions)} functions:")
            for func in functions:
                print(f"  - {func['proname']}()")

        await conn.close()

    except Exception as e:
        print(f"\n✗ Error executing schema: {e}")
        sys.exit(1)


async def test_connection():
    """Test database connection."""
    print("\n" + "="*60)
    print("Testing database connection...")
    print("="*60)

    try:
        from backend.database.database import Database

        db = Database(Config.DATABASE_URL)
        await db.connect()

        # Test query
        async with db.pool.acquire() as conn:
            version = await conn.fetchval('SELECT version()')
            print(f"\n✓ Connected to PostgreSQL")
            print(f"  Version: {version.split(',')[0]}")

            # Count tables
            table_count = await conn.fetchval(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
            )
            print(f"  Tables: {table_count}")

            # Get first strategy
            strategy = await conn.fetchrow("SELECT * FROM strategies LIMIT 1")
            if strategy:
                print(f"\n✓ Default strategy found:")
                print(f"  ID: {strategy['id']}")
                print(f"  Name: {strategy['name']}")
                print(f"  Type: {strategy['type']}")
                print(f"  Mode: {strategy['mode']}")

        await db.disconnect()

        print("\n" + "="*60)
        print("✓ Database setup complete!")
        print("="*60)

    except Exception as e:
        print(f"\n✗ Connection test failed: {e}")
        sys.exit(1)


async def main():
    """Main setup function."""
    print("\n" + "="*60)
    print("XCoin Scalping Bot - Database Setup")
    print("="*60 + "\n")

    # Print configuration
    print("Configuration:")
    print(f"  Database URL: {Config.DATABASE_URL.split('@')[1] if '@' in Config.DATABASE_URL else Config.DATABASE_URL}")
    print(f"  Connection Pool: {Config.DB_MIN_CONNECTIONS}-{Config.DB_MAX_CONNECTIONS}")
    print()

    # Step 1: Create database
    await create_database_if_not_exists()

    # Step 2: Run schema
    await run_schema()

    # Step 3: Test connection
    await test_connection()

    print("\nNext steps:")
    print("  1. Review the .env file and update Zerodha credentials")
    print("  2. Test the database connection:")
    print("     python scripts/test_database.py")
    print("  3. Start implementing the OrderManager")
    print()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

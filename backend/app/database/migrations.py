"""
Database migration utilities for the AI System Design Learning Platform.
"""

import logging
import os
from typing import List, Dict, Any

from sqlalchemy import text, inspect
from sqlalchemy.engine import Engine

from .connection import get_engine, Base
from .models import User, LearningSession, Assessment, Progress, Artifact, SystemMetric, FeatureFlag

logger = logging.getLogger(__name__)


class DatabaseMigration:
    """Handle database migrations and schema updates."""
    
    def __init__(self):
        self.engine = get_engine()
    
    def get_current_schema_version(self) -> str:
        """Get the current schema version from the database."""
        try:
            with self.engine.connect() as connection:
                # Create schema_version table if it doesn't exist (SQLite compatible)
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS schema_version (
                        version VARCHAR(20) PRIMARY KEY,
                        applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        description TEXT
                    )
                """))
                connection.commit()
                
                # Get latest version
                result = connection.execute(text("""
                    SELECT version FROM schema_version 
                    ORDER BY applied_at DESC 
                    LIMIT 1
                """))
                row = result.fetchone()
                return row[0] if row else "0.0.0"
        except Exception as e:
            logger.error(f"Error getting schema version: {e}")
            return "0.0.0"
    
    def set_schema_version(self, version: str, description: str = "") -> None:
        """Set the current schema version."""
        try:
            with self.engine.connect() as connection:
                # Use INSERT OR REPLACE for SQLite compatibility
                connection.execute(text("""
                    INSERT OR REPLACE INTO schema_version (version, description, applied_at) 
                    VALUES (:version, :description, CURRENT_TIMESTAMP)
                """), {"version": version, "description": description})
                connection.commit()
                logger.info(f"Schema version updated to {version}")
        except Exception as e:
            logger.error(f"Error setting schema version: {e}")
            raise
    
    def check_tables_exist(self) -> Dict[str, bool]:
        """Check which tables exist in the database."""
        inspector = inspect(self.engine)
        existing_tables = inspector.get_table_names()
        
        expected_tables = [
            "users", "learning_sessions", "assessments", 
            "progress", "artifacts", "system_metrics", "feature_flags"
        ]
        
        return {table: table in existing_tables for table in expected_tables}
    
    def create_initial_schema(self) -> None:
        """Create the initial database schema."""
        logger.info("Creating initial database schema...")
        
        try:
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            
            # Set initial schema version
            self.set_schema_version("1.0.0", "Initial schema creation")
            
            logger.info("Initial schema created successfully")
            
        except Exception as e:
            logger.error(f"Error creating initial schema: {e}")
            raise
    
    def migrate_to_latest(self) -> None:
        """Migrate database to the latest schema version."""
        current_version = self.get_current_schema_version()
        logger.info(f"Current schema version: {current_version}")
        
        # Define migration steps
        migrations = [
            ("1.0.0", self._migrate_to_1_0_0),
            ("1.1.0", self._migrate_to_1_1_0),
            ("1.2.0", self._migrate_to_1_2_0),
        ]
        
        for version, migration_func in migrations:
            if self._version_less_than(current_version, version):
                logger.info(f"Applying migration to version {version}")
                migration_func()
                current_version = version
        
        logger.info("Database migrations completed")
    
    def _version_less_than(self, current: str, target: str) -> bool:
        """Compare version strings."""
        current_parts = [int(x) for x in current.split(".")]
        target_parts = [int(x) for x in target.split(".")]
        
        # Pad with zeros if needed
        max_len = max(len(current_parts), len(target_parts))
        current_parts += [0] * (max_len - len(current_parts))
        target_parts += [0] * (max_len - len(target_parts))
        
        return current_parts < target_parts
    
    def _migrate_to_1_0_0(self) -> None:
        """Migration to version 1.0.0 - Initial schema."""
        self.create_initial_schema()
    
    def _migrate_to_1_1_0(self) -> None:
        """Migration to version 1.1.0 - Add performance indexes."""
        logger.info("Adding performance indexes...")
        
        try:
            with self.engine.connect() as connection:
                # Add composite indexes for better query performance
                connection.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_sessions_user_status 
                    ON learning_sessions(user_id, status);
                """))
                
                connection.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_assessments_user_created 
                    ON assessments(user_id, created_at DESC);
                """))
                
                connection.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_artifacts_session_type 
                    ON artifacts(session_id, artifact_type);
                """))
                
                connection.commit()
            
            self.set_schema_version("1.1.0", "Added performance indexes")
            
        except Exception as e:
            logger.error(f"Error in migration 1.1.0: {e}")
            raise
    
    def _migrate_to_1_2_0(self) -> None:
        """Migration to version 1.2.0 - Add monitoring columns."""
        logger.info("Adding monitoring and observability columns...")
        
        try:
            with self.engine.connect() as connection:
                # SQLite requires adding columns one at a time
                try:
                    connection.execute(text("ALTER TABLE learning_sessions ADD COLUMN cost_tracking TEXT DEFAULT '{}'"))
                except Exception:
                    pass  # Column might already exist
                
                try:
                    connection.execute(text("ALTER TABLE learning_sessions ADD COLUMN error_count INTEGER DEFAULT 0"))
                except Exception:
                    pass
                
                try:
                    connection.execute(text("ALTER TABLE learning_sessions ADD COLUMN performance_metrics TEXT DEFAULT '{}'"))
                except Exception:
                    pass
                
                try:
                    connection.execute(text("ALTER TABLE users ADD COLUMN total_cost DECIMAL(10,4) DEFAULT 0.0"))
                except Exception:
                    pass
                
                try:
                    connection.execute(text("ALTER TABLE users ADD COLUMN subscription_tier VARCHAR(50) DEFAULT 'free'"))
                except Exception:
                    pass
                
                connection.commit()
            
            self.set_schema_version("1.2.0", "Added monitoring and analytics columns")
            
        except Exception as e:
            logger.error(f"Error in migration 1.2.0: {e}")
            raise


def initialize_database() -> None:
    """Initialize the database for production use."""
    logger.info("Initializing production database...")
    
    migration = DatabaseMigration()
    
    # Check if database is empty
    tables_exist = migration.check_tables_exist()
    
    if not any(tables_exist.values()):
        logger.info("Database is empty, creating initial schema...")
        migration.create_initial_schema()
    else:
        logger.info("Database exists, checking for migrations...")
        migration.migrate_to_latest()
    
    # Create initial data if needed
    _create_initial_data()
    
    logger.info("Database initialization completed")


def _create_initial_data() -> None:
    """Create initial data for the application."""
    from .connection import get_database_session
    
    try:
        with get_database_session() as db:
            # Create default feature flags
            default_flags = [
                {
                    "flag_name": "enable_voice_features",
                    "description": "Enable voice input/output features",
                    "is_enabled": True,
                    "rollout_percentage": 100.0
                },
                {
                    "flag_name": "enable_diagram_generation", 
                    "description": "Enable AI diagram generation",
                    "is_enabled": True,
                    "rollout_percentage": 100.0
                },
                {
                    "flag_name": "enable_advanced_analytics",
                    "description": "Enable advanced progress analytics",
                    "is_enabled": False,
                    "rollout_percentage": 0.0
                }
            ]
            
            for flag_data in default_flags:
                existing_flag = db.query(FeatureFlag).filter(
                    FeatureFlag.flag_name == flag_data["flag_name"]
                ).first()
                
                if not existing_flag:
                    flag = FeatureFlag(**flag_data)
                    db.add(flag)
            
            db.commit()
            logger.info("Initial feature flags created")
            
    except Exception as e:
        logger.error(f"Error creating initial data: {e}")


def backup_database() -> str:
    """Create a database backup."""
    import subprocess
    from datetime import datetime
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not configured")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_{timestamp}.sql"
    
    try:
        # Use pg_dump to create backup
        cmd = [
            "pg_dump",
            "--no-password",
            "--clean",
            "--create",
            "--format=plain",
            "--file", backup_filename,
            database_url
        ]
        
        subprocess.run(cmd, check=True)
        logger.info(f"Database backup created: {backup_filename}")
        return backup_filename
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Database backup failed: {e}")
        raise


if __name__ == "__main__":
    # Command line interface for migrations
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "init":
            initialize_database()
        elif command == "migrate":
            migration = DatabaseMigration()
            migration.migrate_to_latest()
        elif command == "backup":
            backup_database()
        else:
            print("Usage: python migrations.py [init|migrate|backup]")
    else:
        print("Usage: python migrations.py [init|migrate|backup]")
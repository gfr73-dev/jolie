USE JOLIE;

-- Add role columns only when they are missing from an existing installation.
SET @has_master_admin = (
  SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema = DATABASE() AND table_name = 'register_users'
    AND column_name = 'is_master_admin'
);
SET @ddl = IF(@has_master_admin = 0,
  'ALTER TABLE register_users ADD COLUMN is_master_admin BOOLEAN NOT NULL DEFAULT FALSE',
  'SELECT 1'
);
PREPARE migration_stmt FROM @ddl;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @has_can_register = (
  SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema = DATABASE() AND table_name = 'register_users'
    AND column_name = 'is_can_register'
);
SET @ddl = IF(@has_can_register = 0,
  'ALTER TABLE register_users ADD COLUMN is_can_register BOOLEAN NOT NULL DEFAULT FALSE',
  'SELECT 1'
);
PREPARE migration_stmt FROM @ddl;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

-- Creates the archive table with the same columns and indexes as the live table.
CREATE TABLE IF NOT EXISTS register_request_his LIKE register_request;

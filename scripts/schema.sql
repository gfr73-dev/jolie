CREATE DATABASE IF NOT EXISTS JOLIE CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE JOLIE;

CREATE TABLE IF NOT EXISTS register_users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(255) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  user_dir_reg VARCHAR(255) NULL,
  is_admin BOOLEAN NOT NULL DEFAULT FALSE,
  is_master_admin BOOLEAN NOT NULL DEFAULT FALSE,
  is_dir_reg BOOLEAN NOT NULL DEFAULT FALSE,
  is_can_register BOOLEAN NOT NULL DEFAULT FALSE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS register_it_tech (
  id INT AUTO_INCREMENT PRIMARY KEY,
  `Tech User Name` VARCHAR(255) NOT NULL,
  `Tech user email` VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS installation_types (
  id INT AUTO_INCREMENT PRIMARY KEY,
  installation_type VARCHAR(120) NOT NULL,
  printer_type VARCHAR(120) NOT NULL,
  printer_initial_status VARCHAR(120) NOT NULL,
  requires_validation BOOLEAN NOT NULL DEFAULT FALSE,
  INDEX ix_installation_types_printer_type (printer_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS install_status (
  id INT AUTO_INCREMENT PRIMARY KEY,
  status VARCHAR(120) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE account_managers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_manager_name VARCHAR(200) NOT NULL,
    account_manager_email VARCHAR(255) NOT NULL UNIQUE,
    account_manager_dir_reg_email VARCHAR(255) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    INDEX idx_mgr_email (account_manager_email)
);

CREATE TABLE IF NOT EXISTS register_request (
  id INT AUTO_INCREMENT PRIMARY KEY,
  docuid VARCHAR(64) NOT NULL UNIQUE,
  qty VARCHAR(20) NOT NULL DEFAULT '1',
  createdby VARCHAR(255) NOT NULL,
  creation DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  install_date DATE NULL,
  status VARCHAR(120) NOT NULL DEFAULT 'POR GRAVAR',
  `INSTALL_TYPE` VARCHAR(120) NULL,
  `ACCOUNT_INSTALL_CHECK` VARCHAR(255) NULL,
  no_values_from_odbc VARCHAR(255) NULL DEFAULT 'ODBC',
  date_schedule DATE NULL,
  time_schedule TIME NULL,
  account VARCHAR(8) NOT NULL UNIQUE,
  ccc VARCHAR(255) NULL,
  name VARCHAR(255) NULL,
  address1 VARCHAR(255) NULL,
  address2 VARCHAR(255) NULL,
  zip VARCHAR(30) NULL,
  city VARCHAR(120) NULL,
  phn VARCHAR(80) NOT NULL,
  contact VARCHAR(160) NOT NULL,
  email VARCHAR(255) NULL,
  gps_n VARCHAR(80) NULL,
  gps_n_1 VARCHAR(80) NULL,
  account_manager VARCHAR(160) NOT NULL,
  account_manager_email VARCHAR(255) NULL,
  account_assist VARCHAR(255) NULL,
  account_dir_reg VARCHAR(255) NULL,
  printer_requested VARCHAR(120) NOT NULL,
  printer_install_type VARCHAR(120) NULL,
  envios_dia VARCHAR(60) NOT NULL,
  printer_requested_qty VARCHAR(20) NOT NULL DEFAULT '1',
  account_it VARCHAR(255) NOT NULL,
  account_it_email VARCHAR(255) NULL,
  account_it_support VARCHAR(255) NULL DEFAULT 'A preencher pelo DSI',
  printer_1 VARCHAR(255) NULL,
  usb_cable_1 VARCHAR(120) NULL DEFAULT '9 Pin Cable',
  `925_adapt_1` VARCHAR(10) NULL DEFAULT 'NO',
  key_1 VARCHAR(255) NULL,
  obs_migracao TEXT NULL,
  normalizada_1 VARCHAR(10) NULL DEFAULT 'NÃO',
  db_ok_1 INT NULL,
  db_nok_1 INT NULL,
  obs_normalizada_1 TEXT NULL,
  requires_printer_validation BOOLEAN NOT NULL DEFAULT FALSE,
  is_printer_validated VARCHAR(30) NULL,
  printer_validation_changed_by VARCHAR(255) NULL,
  printer_validation_changed_at DATETIME NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX ix_register_request_status (status),
  INDEX ix_register_request_account (account)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Keep the archive table structurally identical to the active request table.
CREATE TABLE IF NOT EXISTS register_request_his LIKE register_request;

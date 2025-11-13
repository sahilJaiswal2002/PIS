-- MySQL schema for PIS application
-- Database: pis

CREATE DATABASE IF NOT EXISTS `pis` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE `pis`;

-- ===== Users =====
CREATE TABLE IF NOT EXISTS `user` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(80) NOT NULL,
  `email` VARCHAR(120) NOT NULL,
  `password` VARCHAR(255) NOT NULL,
  `is_admin` TINYINT(1) NOT NULL DEFAULT 0,
  `requested_admin` TINYINT(1) NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_user_username` (`username`),
  UNIQUE KEY `uq_user_email` (`email`),
  KEY `ix_user_requested_admin` (`requested_admin`),
  KEY `ix_user_admin_req` (`requested_admin`, `is_admin`)
) ENGINE=InnoDB;

-- ===== Diseases =====
CREATE TABLE IF NOT EXISTS `disease` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `description` TEXT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

-- ===== Hospitals =====
CREATE TABLE IF NOT EXISTS `hospital` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `address` TEXT NULL,
  `phone` VARCHAR(20) NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

-- ===== Doctors =====
CREATE TABLE IF NOT EXISTS `doctor` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `specialization` VARCHAR(100) NULL,
  `hospital_id` INT NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_doctor_hospital_id` (`hospital_id`),
  CONSTRAINT `fk_doctor_hospital` FOREIGN KEY (`hospital_id`)
    REFERENCES `hospital` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ===== Doctor <-> Disease (many-to-many) =====
CREATE TABLE IF NOT EXISTS `doctor_diseases` (
  `doctor_id` INT NOT NULL,
  `disease_id` INT NOT NULL,
  PRIMARY KEY (`doctor_id`, `disease_id`),
  KEY `ix_dd_disease_id` (`disease_id`),
  CONSTRAINT `fk_dd_doctor` FOREIGN KEY (`doctor_id`)
    REFERENCES `doctor` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_dd_disease` FOREIGN KEY (`disease_id`)
    REFERENCES `disease` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ===== Forms =====
CREATE TABLE IF NOT EXISTS `form` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `description` TEXT NULL,
  `disease_id` INT NOT NULL,
  `version` INT NOT NULL DEFAULT 1,
  `is_active` TINYINT(1) NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_form_disease_id` (`disease_id`),
  CONSTRAINT `fk_form_disease` FOREIGN KEY (`disease_id`)
    REFERENCES `disease` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ===== Form fields (dynamic) =====
CREATE TABLE IF NOT EXISTS `form_field` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `form_id` INT NOT NULL,
  `field_name` VARCHAR(100) NOT NULL,
  `field_type` VARCHAR(50) NOT NULL,
  `field_label` VARCHAR(200) NOT NULL,
  `is_required` TINYINT(1) NOT NULL DEFAULT 0,
  `options` TEXT NULL,
  `order` INT NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_form_field_form_id` (`form_id`),
  CONSTRAINT `fk_form_field_form` FOREIGN KEY (`form_id`)
    REFERENCES `form` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ===== Form versioning =====
CREATE TABLE IF NOT EXISTS `form_version` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `form_id` INT NOT NULL,
  `version_number` INT NOT NULL,
  `fields_snapshot` TEXT NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by_id` INT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_form_version_form_id` (`form_id`),
  KEY `ix_form_version_created_by_id` (`created_by_id`),
  CONSTRAINT `fk_form_version_form` FOREIGN KEY (`form_id`)
    REFERENCES `form` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_form_version_user` FOREIGN KEY (`created_by_id`)
    REFERENCES `user` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ===== Submissions =====
CREATE TABLE IF NOT EXISTS `submission` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `form_id` INT NOT NULL,
  `disease_id` INT NOT NULL,
  `hospital_id` INT NOT NULL,
  `doctor_id` INT NOT NULL,
  `data` TEXT NOT NULL,
  `form_version` INT NOT NULL DEFAULT 1,
  `status` VARCHAR(50) NOT NULL DEFAULT 'submitted',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_submission_user_id` (`user_id`),
  KEY `ix_submission_form_id` (`form_id`),
  KEY `ix_submission_disease_id` (`disease_id`),
  KEY `ix_submission_hospital_id` (`hospital_id`),
  KEY `ix_submission_doctor_id` (`doctor_id`),
  CONSTRAINT `fk_submission_user` FOREIGN KEY (`user_id`)
    REFERENCES `user` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_submission_form` FOREIGN KEY (`form_id`)
    REFERENCES `form` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_submission_disease` FOREIGN KEY (`disease_id`)
    REFERENCES `disease` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_submission_hospital` FOREIGN KEY (`hospital_id`)
    REFERENCES `hospital` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_submission_doctor` FOREIGN KEY (`doctor_id`)
    REFERENCES `doctor` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- NOTE: Submission reviews table intentionally removed per project requirement.

-- ===== Draft submissions =====
CREATE TABLE IF NOT EXISTS `draft_submission` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `form_id` INT NOT NULL,
  `disease_id` INT NOT NULL,
  `hospital_id` INT NOT NULL,
  `doctor_id` INT NOT NULL,
  `data` TEXT NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_draft_user_id` (`user_id`),
  KEY `ix_draft_form_id` (`form_id`),
  KEY `ix_draft_disease_id` (`disease_id`),
  KEY `ix_draft_hospital_id` (`hospital_id`),
  KEY `ix_draft_doctor_id` (`doctor_id`),
  CONSTRAINT `fk_draft_user` FOREIGN KEY (`user_id`)
    REFERENCES `user` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_draft_form` FOREIGN KEY (`form_id`)
    REFERENCES `form` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_draft_disease` FOREIGN KEY (`disease_id`)
    REFERENCES `disease` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_draft_hospital` FOREIGN KEY (`hospital_id`)
    REFERENCES `hospital` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_draft_doctor` FOREIGN KEY (`doctor_id`)
    REFERENCES `doctor` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ===== Audit logs =====
CREATE TABLE IF NOT EXISTS `audit_log` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `action` VARCHAR(255) NOT NULL,
  `entity_type` VARCHAR(50) NOT NULL,
  `entity_id` INT NULL,
  `entity_name` VARCHAR(255) NULL,
  `details` TEXT NULL,
  `ip_address` VARCHAR(45) NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_audit_user_id` (`user_id`),
  KEY `ix_audit_entity` (`entity_type`, `entity_id`),
  CONSTRAINT `fk_audit_user` FOREIGN KEY (`user_id`)
    REFERENCES `user` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ===== Security questions =====
CREATE TABLE IF NOT EXISTS `security_question` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `question` VARCHAR(255) NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

-- ===== User answers to security questions =====
CREATE TABLE IF NOT EXISTS `user_security_question` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `question_id` INT NOT NULL,
  `answer` VARCHAR(255) NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_usq_user_id` (`user_id`),
  KEY `ix_usq_question_id` (`question_id`),
  CONSTRAINT `fk_usq_user` FOREIGN KEY (`user_id`)
    REFERENCES `user` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_usq_question` FOREIGN KEY (`question_id`)
    REFERENCES `security_question` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ===== Password reset tokens =====
CREATE TABLE IF NOT EXISTS `password_reset_token` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `token` VARCHAR(255) NOT NULL,
  `is_verified` TINYINT(1) NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `expires_at` DATETIME NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_reset_token` (`token`),
  KEY `ix_reset_user_id` (`user_id`),
  CONSTRAINT `fk_reset_user` FOREIGN KEY (`user_id`)
    REFERENCES `user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB;
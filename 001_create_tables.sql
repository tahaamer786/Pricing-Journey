-- ============================================================
-- Jubala Onboarding & Pricing — Full Database Migration
-- ============================================================

CREATE DATABASE IF NOT EXISTS jubala_onboarding_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE jubala_onboarding_db;

-- ── onboarding_users ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS onboarding_users (
    id                    VARCHAR(8)    NOT NULL PRIMARY KEY,
    google_id             VARCHAR(255)  NOT NULL UNIQUE,
    email                 VARCHAR(255)  NOT NULL UNIQUE,
    first_name            VARCHAR(150)  NULL,
    last_name             VARCHAR(150)  NULL,
    profile_picture_url   VARCHAR(500)  NULL,
    company_url           VARCHAR(500)  NULL,
    selected_plan_id      VARCHAR(8)    NULL,
    created_at            DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at            DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_google_id (google_id),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── plans ──────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS plans (
    id                              VARCHAR(8)     NOT NULL PRIMARY KEY,
    name                            VARCHAR(100)   NOT NULL,
    price                           DECIMAL(10,2)  NULL,
    price_label                     VARCHAR(50)    NULL,
    minutes_included                INT            NULL,
    minutes_label                   VARCHAR(100)   NULL,
    setup_fee                       DECIMAL(10,2)  NULL,
    is_free_for_founding_clients    BOOLEAN        NOT NULL DEFAULT FALSE,
    founding_client_start_date      DATE           NULL,
    founding_client_end_date        DATE           NULL,
    is_custom                       BOOLEAN        NOT NULL DEFAULT FALSE,
    is_most_popular                 BOOLEAN        NOT NULL DEFAULT FALSE,
    button_text                     VARCHAR(100)   NOT NULL DEFAULT 'Start free',
    display_order                   INT            NOT NULL DEFAULT 0,
    is_active                       BOOLEAN        NOT NULL DEFAULT TRUE,
    icon                            VARCHAR(50)    NULL,
    created_at                      DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at                      DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_display_order (display_order),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── plan_features ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS plan_features (
    id              VARCHAR(8)    NOT NULL PRIMARY KEY,
    plan_id         VARCHAR(8)    NOT NULL,
    feature_text    VARCHAR(300)  NOT NULL,
    is_included     BOOLEAN       NOT NULL DEFAULT TRUE,
    display_order   INT           NOT NULL DEFAULT 0,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plan_id) REFERENCES plans(id) ON DELETE CASCADE,
    INDEX idx_plan_id (plan_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── onboarding_questions ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS onboarding_questions (
    id              VARCHAR(8)    NOT NULL PRIMARY KEY,
    question_text   VARCHAR(500)  NOT NULL,
    display_order   INT           NOT NULL DEFAULT 0,
    is_active       BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_display_order (display_order),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── persona_reports ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS persona_reports (
    id              VARCHAR(8)                          NOT NULL PRIMARY KEY,
    user_id         VARCHAR(8)                          NOT NULL,
    source_type     ENUM('url', 'questions')             NOT NULL,
    company_url     VARCHAR(500)                        NULL,
    persona_json    JSON                                NOT NULL,
    status          ENUM('pending_call', 'called')       NOT NULL DEFAULT 'pending_call',
    called_at       DATETIME                            NULL,
    call_notes      TEXT                                NULL,
    created_at      DATETIME                            NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME                            NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES onboarding_users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── persona_qa ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS persona_qa (
    id              VARCHAR(8)    NOT NULL PRIMARY KEY,
    persona_id      VARCHAR(8)    NOT NULL,
    question        VARCHAR(500)  NOT NULL,
    answer          TEXT          NOT NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (persona_id) REFERENCES persona_reports(id) ON DELETE CASCADE,
    INDEX idx_persona_id (persona_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Seed: 4 default plans (Starter, Essential, Professional, Custom)
-- ============================================================

INSERT INTO plans (id, name, price, minutes_included, setup_fee, is_free_for_founding_clients,
    founding_client_start_date, founding_client_end_date, is_custom, is_most_popular,
    button_text, display_order, icon)
VALUES
('pln00001', 'Starter', 99.00, 500, 500.00, TRUE, '2026-07-08', '2026-10-06', FALSE, FALSE, 'Get Starter $99/mo', 1, 'phone'),
('pln00002', 'Essential', 199.00, 1000, 500.00, TRUE, '2026-07-08', '2026-10-06', FALSE, FALSE, 'Get Essential $199/mo', 2, 'mic'),
('pln00003', 'Professional', 399.00, 2000, 750.00, TRUE, '2026-07-08', '2026-10-06', FALSE, TRUE, 'Get Professional $399/mo', 3, 'star'),
('pln00004', 'Custom', NULL, NULL, NULL, FALSE, NULL, NULL, TRUE, FALSE, 'Contact us', 4, 'building');

UPDATE plans SET price_label = 'Custom pricing', minutes_label = 'Custom minute package' WHERE id = 'pln00004';

-- Starter features (5)
INSERT INTO plan_features (id, plan_id, feature_text, is_included, display_order) VALUES
('feat0001', 'pln00001', '500 included minutes per month', TRUE, 1),
('feat0002', 'pln00001', 'AI voice agent for inbound calls', TRUE, 2),
('feat0003', 'pln00001', 'Appointment booking & routing', TRUE, 3),
('feat0004', 'pln00001', 'Call summaries & transcripts', TRUE, 4),
('feat0005', 'pln00001', 'Custom setup', TRUE, 5);

-- Essential features (5)
INSERT INTO plan_features (id, plan_id, feature_text, is_included, display_order) VALUES
('feat0006', 'pln00002', '1,000 included minutes per month', TRUE, 1),
('feat0007', 'pln00002', 'Everything in Starter', TRUE, 2),
('feat0008', 'pln00002', 'SMS & email follow-ups', TRUE, 3),
('feat0009', 'pln00002', 'Priority support', TRUE, 4),
('feat0010', 'pln00002', 'Custom setup', TRUE, 5);

-- Professional features (5)
INSERT INTO plan_features (id, plan_id, feature_text, is_included, display_order) VALUES
('feat0011', 'pln00003', '2,000 included minutes per month', TRUE, 1),
('feat0012', 'pln00003', 'Everything in Essential', TRUE, 2),
('feat0013', 'pln00003', 'Multi-workflow automation', TRUE, 3),
('feat0014', 'pln00003', 'Advanced call routing rules', TRUE, 4),
('feat0015', 'pln00003', 'Dedicated onboarding support', TRUE, 5);

-- Custom features (5)
INSERT INTO plan_features (id, plan_id, feature_text, is_included, display_order) VALUES
('feat0016', 'pln00004', 'Custom included minutes & usage', TRUE, 1),
('feat0017', 'pln00004', 'Custom AI voice workflows & scripts', TRUE, 2),
('feat0018', 'pln00004', 'Custom integrations & automations', TRUE, 3),
('feat0019', 'pln00004', 'Custom routing, reporting & analytics', TRUE, 4),
('feat0020', 'pln00004', 'Dedicated onboarding & account support', TRUE, 5);

-- ============================================================
-- Seed: 5 default onboarding questions (used when no URL given)
-- ============================================================

INSERT INTO onboarding_questions (id, question_text, display_order, is_active) VALUES
('q0000001', 'What type of legal services does your firm provide?', 1, TRUE),
('q0000002', 'What is your primary practice area?', 2, TRUE),
('q0000003', 'How many clients do you typically handle per month?', 3, TRUE),
('q0000004', 'What is your biggest challenge in client intake or scheduling?', 4, TRUE),
('q0000005', 'Do you handle international or education/immigration law cases?', 5, TRUE);

-- ============================================================
-- Done! Run: uvicorn main:app --reload --port 8002
-- ============================================================

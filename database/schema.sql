CREATE TABLE IF NOT EXISTS children (
    child_id VARCHAR(64) PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    tokens INT NOT NULL DEFAULT 0,
    selected_character VARCHAR(100) NOT NULL DEFAULT 'fox',
    selected_outfit VARCHAR(100) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS strengths (
    strength_id VARCHAR(64) PRIMARY KEY,
    name_zh VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    suggestion TEXT NOT NULL,
    fruit_name VARCHAR(100) NOT NULL,
    outfit_reward VARCHAR(100) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS child_strengths (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    child_id VARCHAR(64) NOT NULL,
    strength_id VARCHAR(64) NOT NULL,
    source VARCHAR(50) NOT NULL,
    evidence_text TEXT NOT NULL,
    confidence DECIMAL(4,3) NOT NULL DEFAULT 0.700,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_child_strengths_child
        FOREIGN KEY (child_id) REFERENCES children(child_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_child_strengths_strength
        FOREIGN KEY (strength_id) REFERENCES strengths(strength_id)
        ON DELETE CASCADE,
    INDEX idx_child_strengths_child (child_id),
    INDEX idx_child_strengths_strength (strength_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS chat_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    child_id VARCHAR(64) NOT NULL,
    user_message TEXT NOT NULL,
    ai_reply TEXT NOT NULL,
    emotion VARCHAR(100) NULL,
    detected_strengths_json JSON NULL,
    tokens_earned INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_chat_logs_child
        FOREIGN KEY (child_id) REFERENCES children(child_id)
        ON DELETE CASCADE,
    INDEX idx_chat_logs_child_created (child_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id VARCHAR(64) PRIMARY KEY,
    child_id VARCHAR(64) NOT NULL,
    created_at TIMESTAMP NULL,
    closed_at TIMESTAMP NULL,
    messages_json JSON NULL,
    token_events_json JSON NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_chat_sessions_child
        FOREIGN KEY (child_id) REFERENCES children(child_id)
        ON DELETE CASCADE,
    INDEX idx_chat_sessions_child_closed (child_id, closed_at, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS token_transactions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    child_id VARCHAR(64) NOT NULL,
    amount INT NOT NULL,
    reason VARCHAR(80) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_token_transactions_child
        FOREIGN KEY (child_id) REFERENCES children(child_id)
        ON DELETE CASCADE,
    INDEX idx_token_transactions_child_created (child_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS game_sessions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    child_id VARCHAR(64) NOT NULL,
    score INT NOT NULL DEFAULT 0,
    tokens_spent INT NOT NULL DEFAULT 0,
    tokens_earned INT NOT NULL DEFAULT 0,
    fruits_eaten_json JSON NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_game_sessions_child
        FOREIGN KEY (child_id) REFERENCES children(child_id)
        ON DELETE CASCADE,
    INDEX idx_game_sessions_child_created (child_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS game_reflections (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    child_id VARCHAR(64) NOT NULL,
    game_type VARCHAR(40) NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    score_before_game_over INT NOT NULL DEFAULT 0,
    game_over_reason VARCHAR(80) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_game_reflections_child
        FOREIGN KEY (child_id) REFERENCES children(child_id)
        ON DELETE CASCADE,
    INDEX idx_game_reflections_child_created (child_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS outfits (
    outfit_id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    related_strength_id VARCHAR(64) NULL,
    cost INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_outfits_strength
        FOREIGN KEY (related_strength_id) REFERENCES strengths(strength_id)
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS child_outfits (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    child_id VARCHAR(64) NOT NULL,
    outfit_id VARCHAR(100) NOT NULL,
    unlocked_source VARCHAR(80) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_child_outfits_child
        FOREIGN KEY (child_id) REFERENCES children(child_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_child_outfits_outfit
        FOREIGN KEY (outfit_id) REFERENCES outfits(outfit_id)
        ON DELETE CASCADE,
    UNIQUE KEY uq_child_outfit (child_id, outfit_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS todo_items (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    child_id VARCHAR(64) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NULL,
    is_completed BOOLEAN NOT NULL DEFAULT FALSE,
    tokens_reward INT NOT NULL DEFAULT 10,
    due_date DATE NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    CONSTRAINT fk_todo_items_child
        FOREIGN KEY (child_id) REFERENCES children(child_id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS diary_entries (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    child_id VARCHAR(64) NOT NULL,
    content TEXT NOT NULL,
    ai_reply TEXT NULL,
    detected_strengths_json JSON NULL,
    tokens_earned INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_diary_entries_child
        FOREIGN KEY (child_id) REFERENCES children(child_id)
        ON DELETE CASCADE,
    INDEX idx_diary_entries_child_created (child_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

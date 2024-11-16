SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET collation_connection = utf8mb4_unicode_ci;

USE kolang;

DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS chatlist;

CREATE TABLE chatlist (
    chat_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    summary VARCHAR(255) NULL,
    feedback JSON NULL,
    situation VARCHAR(255) NULL,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    completed_at TIMESTAMP(6) NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE messages (
    message_id INT AUTO_INCREMENT PRIMARY KEY,
    chat_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    message VARCHAR(255) NULL,
    is_answer BOOLEAN NOT NULL,
    FOREIGN KEY (chat_id) REFERENCES chatlist(chat_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
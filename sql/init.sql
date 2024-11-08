USE kolang;

DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS chatlist;
DROP TABLE IF EXISTS messages;

CREATE TABLE users (
    user_id VARCHAR(255) PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255) NULL,
    created_at TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP NULL,
    onboarding BOOLEAN NOT NULL,
    onboarding_info JSON NULL
);

CREATE TABLE chatlist (
    chat_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    summary VARCHAR(255) NULL,
    category VARCHAR(255) NULL,
    created_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE messages (
    message_id INT AUTO_INCREMENT PRIMARY KEY,
    chat_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NULL,
    message TEXT NULL,
    is_answer BOOLEAN NOT NULL,
    FOREIGN KEY (chat_id) REFERENCES chatlist(chat_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

INSERT INTO users (user_id, email, name, created_at, deleted_at, onboarding, onboarding_info)
VALUES (
    'test',
    'test@example.com',
    'test',
    NOW(),
    NULL,
    TRUE,
    JSON_ARRAY('Intermediate', 'culture', '30s')
);

INSERT INTO chatlist (chat_id, user_id, summary, category, created_at)
VALUES
('chat_1', 'test', '테스트 채팅방 1', 'test', NOW()),
('chat_2', 'test', '테스트 채팅방 2', 'test', NOW()),
('chat_3', 'test', '테스트 채팅방 3', 'test', NOW()),
('chat_4', 'test', '테스트 채팅방 4', 'test', NOW()),
('chat_5', 'test', '테스트 채팅방 5', 'test', NOW()),
('chat_6', 'test', '테스트 채팅방 6', 'test', NOW()),
('chat_7', 'test', '테스트 채팅방 7', 'test', NOW()),
('chat_8', 'test', '테스트 채팅방 8', 'test', NOW()),
('chat_9', 'test', '테스트 채팅방 9', 'test', NOW()),
('chat_10', 'test', '테스트 채팅방 10', 'test', NOW()),
('chat_11', 'test', '테스트 채팅방 11', 'test', NOW());

INSERT INTO messages (chat_id, user_id, created_at, message, is_answer)
SELECT 
    chat_id,
    'test',
    NOW(),
    CONCAT('테스트 메시지 ', message_num),
    FALSE
FROM 
    chatlist
    CROSS JOIN (SELECT 1 AS message_num UNION SELECT 2 UNION SELECT 3) AS numbers;
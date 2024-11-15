SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET collation_connection = utf8mb4_unicode_ci;

USE kolang;

DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS chatlist;
DROP TABLE IF EXISTS users;

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
    feedback VARCHAR(255) NULL,
    situation VARCHAR(255) NULL,
    created_at TIMESTAMP NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
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

INSERT INTO users (user_id, email, name, created_at, onboarding, onboarding_info)
VALUES (
    '908621d3-337c-46b3-a6d0-177c97ede9db',
    'saine0501@gmail.com',
    '빈',
    NOW(),
    TRUE,
    JSON_ARRAY('Intermediate', 'culture', '20s')
);

INSERT INTO chatlist (chat_id, user_id, summary, feedback, situation, created_at, active)
SELECT 
    CONCAT('chat_', situation, '_', num) as chat_id,
    '908621d3-337c-46b3-a6d0-177c97ede9db' as user_id,
    CONCAT(situation, ' 테스트 대화 ', num) as summary,
    '발음과 어순 교정 필요' as feedback,
    situation,
    NOW() as created_at,
    TRUE as active
FROM 
    (SELECT 'shopping' as situation UNION ALL 
     SELECT 'travel' UNION ALL 
     SELECT 'airport' UNION ALL 
     SELECT 'korean_class') situations
CROSS JOIN
    (SELECT 1 as num UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL 
     SELECT 4 UNION ALL SELECT 5) numbers;

INSERT INTO messages (chat_id, user_id, created_at, message, is_answer)
WITH RECURSIVE message_templates AS (
    SELECT 1 as msg_order, '안녕하세요' as user_msg, '안녕하세요! 무엇을 도와드릴까요?' as system_msg
    UNION ALL
    SELECT 2, '{{situation}}에 대해 물어보고 싶어요', '{{situation}}에 대해 알려드리겠습니다'
    UNION ALL
    SELECT 3, '감사합니다', '별말씀을요. 더 궁금한 점 있으시면 언제든 물어보세요!'
)
SELECT chat_id, 
       '908621d3-337c-46b3-a6d0-177c97ede9db',
       NOW(),
       REPLACE(user_msg, '{{situation}}', situation),
       FALSE
FROM chatlist
CROSS JOIN message_templates
UNION ALL
SELECT chat_id,
       '908621d3-337c-46b3-a6d0-177c97ede9db',
       NOW(),
       REPLACE(system_msg, '{{situation}}', situation),
       TRUE
FROM chatlist
CROSS JOIN message_templates
ORDER BY chat_id, msg_order;
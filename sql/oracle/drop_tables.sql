SELECT 'DROP TABLE ' || table_name || ';'
FROM user_tables
WHERE table_name LIKE 'your_prefix_%';

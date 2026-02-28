-- File: seeds/generate_data.sql
-- This script generates 10 million records for the users table efficiently.

INSERT INTO users (name, email, country_code, subscription_tier, lifetime_value, signup_date)
SELECT 
    'User_' || i AS name,
    'user_' || i || '@example.com' AS email,
    (ARRAY['US', 'GB', 'CA', 'DE', 'FR', 'JP', 'AU', 'BR', 'IN', 'CN'])[floor(random() * 10) + 1] AS country_code,
    (ARRAY['free', 'basic', 'premium', 'enterprise'])[floor(random() * 4) + 1] AS subscription_tier,
    round((random() * 1000)::numeric, 2) AS lifetime_value,
    now() - (random() * interval '365 days') AS signup_date
FROM generate_series(1, 10000000) s(i);

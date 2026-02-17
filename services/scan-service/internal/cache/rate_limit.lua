-- Atomic Rate Limiter using Redis Sorted Set
-- Implements sliding window algorithm with atomic operations
--
-- KEYS[1] = rate limit key (e.g., "ratelimit:ip:192.168.1.1")
-- ARGV[1] = current timestamp (milliseconds)
-- ARGV[2] = window start timestamp (current - 60000 for 1 minute)
-- ARGV[3] = limit (max requests per window)
-- ARGV[4] = unique request ID (for ZADD member)
-- ARGV[5] = TTL in seconds (for key expiration)
--
-- Returns:
-- 1 = allowed
-- 0 = rate limit exceeded

local key = KEYS[1]
local now = tonumber(ARGV[1])
local window_start = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local request_id = ARGV[4]
local ttl = tonumber(ARGV[5])

-- Remove old entries outside the sliding window
redis.call('ZREMRANGEBYSCORE', key, 0, window_start)

-- Count current requests in window
local current_count = redis.call('ZCARD', key)

-- Check if limit exceeded
if current_count >= limit then
    return 0
end

-- Add current request to sorted set
redis.call('ZADD', key, now, request_id)

-- Set expiration to prevent memory leak
redis.call('EXPIRE', key, ttl)

return 1

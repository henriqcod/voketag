-- Atomic Idempotency Key Storage using Lua Script
-- Ensures true atomicity for set-if-not-exists operations
-- Works correctly with Redis Cluster (single key operation)

local key = KEYS[1]
local request_hash = ARGV[1]
local response_payload = ARGV[2]
local status_code = ARGV[3]
local created_at = ARGV[4]
local ttl = tonumber(ARGV[5])

-- Check if key exists
if redis.call("EXISTS", key) == 1 then
    -- Key exists - return existing data
    local existing = redis.call("HGETALL", key)
    
    -- Convert flat array to table
    local result = {}
    for i = 1, #existing, 2 do
        result[existing[i]] = existing[i + 1]
    end
    
    -- Return 0 to indicate key already exists
    -- Client will check request_hash to determine if it's same request or conflict
    return {0, result["request_hash"], result["response_payload"], result["status_code"]}
else
    -- Key doesn't exist - create it atomically
    redis.call("HSET", key, 
        "request_hash", request_hash,
        "response_payload", response_payload,
        "status_code", status_code,
        "created_at", created_at
    )
    redis.call("EXPIRE", key, ttl)
    
    -- Return 1 to indicate new key created
    return {1, "", "", ""}
end

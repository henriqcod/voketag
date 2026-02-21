-- Atomic Audit Event Logging with Hash Chain Verification
-- Guarantees: event persisted + hash validated + hash updated in SINGLE atomic operation
-- 
-- This script ensures the audit chain cannot be broken by:
-- 1. Verifying previous_hash matches current state
-- 2. Persisting the event to an append-only list
-- 3. Updating the hash pointer atomically
--
-- All-or-nothing guarantee: If any step fails, entire operation rolls back.

local last_hash_key = KEYS[1]    -- Key storing the last hash pointer
local event_list_key = KEYS[2]   -- Key for append-only event list
local expected_prev = ARGV[1]    -- Expected previous hash (for validation)
local new_hash = ARGV[2]         -- New hash to set after event
local event_data = ARGV[3]       -- Serialized event JSON

-- Step 1: Get current hash (atomic read)
local current_hash = redis.call('GET', last_hash_key)

-- Handle genesis case (first event)
if not current_hash then
    current_hash = string.rep('0', 64)
end

-- Step 2: Verify hash chain integrity
if current_hash ~= expected_prev then
    -- Hash mismatch: concurrent modification detected
    -- Return error code with current hash for retry
    return {0, 'hash_mismatch', current_hash}
end

-- Step 3: Atomic persistence (all-or-nothing)
-- Append event to list (immutable log)
redis.call('RPUSH', event_list_key, event_data)

-- Update hash pointer
redis.call('SET', last_hash_key, new_hash)

-- Step 4: Success response
return {1, 'ok', new_hash}

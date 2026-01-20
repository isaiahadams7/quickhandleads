-- Migration to add api_queries_used column to search_history table
-- Run this in your Supabase SQL Editor

ALTER TABLE search_history
ADD COLUMN IF NOT EXISTS api_queries_used INTEGER DEFAULT 0;

-- Update existing rows to have 0 for api_queries_used if NULL
UPDATE search_history
SET api_queries_used = 0
WHERE api_queries_used IS NULL;

-- Add location_match flag to leads
ALTER TABLE leads
ADD COLUMN IF NOT EXISTS location_match BOOLEAN DEFAULT FALSE;

ALTER TABLE leads
ADD COLUMN IF NOT EXISTS intent_match BOOLEAN DEFAULT FALSE;

ALTER TABLE leads
ADD COLUMN IF NOT EXISTS lead_source TEXT;

ALTER TABLE leads
ADD COLUMN IF NOT EXISTS post_created_at TIMESTAMP;

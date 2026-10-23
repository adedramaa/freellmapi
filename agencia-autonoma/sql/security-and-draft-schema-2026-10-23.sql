-- AUTÓNOMA DEV: idempotent supporting schema for intake throttling and commercial drafts.
-- No credentials or real client data. Test on a Neon preview branch before restoring.
CREATE TABLE IF NOT EXISTS agencia.lead_submission_locks(
 email_hash char(64) PRIMARY KEY,
 last_submitted_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS lead_submission_locks_recent_idx
 ON agencia.lead_submission_locks(last_submitted_at DESC);

-- Only one non-closed payment preparation per approved quote.
-- These records do NOT represent proof of banking receipt.
CREATE UNIQUE INDEX IF NOT EXISTS agency_one_active_payment_request_per_quote
 ON agencia.payment_intents(quote_id)
 WHERE state NOT IN ('cancelled','rejected','refunded');

-- Hourly monitor stores only totals, no personal details.
CREATE TABLE IF NOT EXISTS agencia.monitor_snapshots(
 slot timestamptz PRIMARY KEY,
 checked_at timestamptz NOT NULL DEFAULT now(),
 website_ok boolean NOT NULL,
 backend_ok boolean NOT NULL,
 pending_leads integer NOT NULL DEFAULT 0,
 total_leads integer NOT NULL DEFAULT 0,
 error_flags jsonb NOT NULL DEFAULT '[]'::jsonb,
 CHECK(pending_leads>=0 AND total_leads>=0)
);
CREATE INDEX IF NOT EXISTS monitor_snapshots_checked_idx
 ON agencia.monitor_snapshots(checked_at DESC);

-- Periodic hygiene: run by the hourly Neon Function, never by public visitors.
-- DELETE FROM agencia.lead_submission_locks
-- WHERE last_submitted_at < now() - interval '24 hours';

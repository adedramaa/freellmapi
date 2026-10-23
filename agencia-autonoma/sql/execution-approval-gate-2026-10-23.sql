-- Execution state guard for Autónoma Dev: captured 2026-10-23 23:40 UTC.
-- Restore on staging after the base agencia schema is installed.
-- These fields record internal attestations, NOT independently verified repository privacy, legal compliance or bank settlement.
-- Do not run Claude Code or spend money based on this SQL file alone.
ALTER TABLE agencia.work_orders ADD COLUMN IF NOT EXISTS private_repo_checked_at timestamptz;
ALTER TABLE agencia.work_orders ADD COLUMN IF NOT EXISTS private_repo_checked_by varchar(160);
ALTER TABLE agencia.work_orders ADD COLUMN IF NOT EXISTS tax_reviewed_at timestamptz;
ALTER TABLE agencia.work_orders ADD COLUMN IF NOT EXISTS tax_reviewed_by varchar(160);
ALTER TABLE agencia.work_orders ADD COLUMN IF NOT EXISTS execution_approved_at timestamptz;
ALTER TABLE agencia.work_orders ADD COLUMN IF NOT EXISTS execution_approved_by varchar(160);
ALTER TABLE agencia.work_orders ADD COLUMN IF NOT EXISTS max_ai_cost_usd_cents integer CHECK(max_ai_cost_usd_cents IS NULL OR max_ai_cost_usd_cents>=0);
ALTER TABLE agencia.work_orders ADD COLUMN IF NOT EXISTS run_expiry_at timestamptz;
CREATE OR REPLACE FUNCTION agencia.guard_work_order()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE quote_rec record;
BEGIN
 IF TG_OP='INSERT' AND NEW.status<>'blocked' THEN RAISE EXCEPTION 'New work order must begin blocked'; END IF;
 SELECT src.lead_id,src.stage,src.quote_currency,src.quote_amount_minor INTO quote_rec
 FROM agencia.quote_drafts src WHERE src.id=NEW.quote_id;
 IF quote_rec.lead_id IS DISTINCT FROM NEW.lead_id OR quote_rec.stage <> 'enviado' THEN
  RAISE EXCEPTION 'Work order requires approved quote'; END IF;
 IF NOT EXISTS (SELECT 1 FROM agencia.payment_intents p
 WHERE p.lead_id=NEW.lead_id AND p.quote_id=NEW.quote_id AND p.state='verified'
 AND p.received_minor>=quote_rec.quote_amount_minor AND p.currency=quote_rec.quote_currency)
 THEN RAISE EXCEPTION 'Development requires reconciled payment'; END IF;
 IF (SELECT status FROM agencia.leads WHERE id=NEW.lead_id) NOT IN ('aprobado','en_produccion')
 THEN RAISE EXCEPTION 'Lead must be accepted'; END IF;
 IF NEW.approved_by IS NULL OR NEW.approved_at IS NULL OR NEW.spec='{}'::jsonb THEN
  RAISE EXCEPTION 'Owner approval and specification required'; END IF;
 IF TG_OP='UPDATE' AND NEW.status<>OLD.status THEN
  IF NOT (
   (OLD.status='queued' AND NEW.status IN ('plan_ready','blocked','cancelled')) OR
   (OLD.status='plan_ready' AND NEW.status IN ('building','blocked','cancelled')) OR
   (OLD.status='building' AND NEW.status IN ('qa_pending','blocked','cancelled')) OR
   (OLD.status='qa_pending' AND NEW.status IN ('qa_passed','building','blocked')) OR
   (OLD.status='qa_passed' AND NEW.status IN ('ready_for_review','building','blocked')) OR
   (OLD.status='ready_for_review' AND NEW.status IN ('approved_for_delivery','building','blocked')) OR
   (OLD.status='approved_for_delivery' AND NEW.status='delivered') OR
   (OLD.status='blocked' AND NEW.status IN ('plan_ready','cancelled'))
  ) THEN RAISE EXCEPTION 'Work status transition not allowed'; END IF;
 END IF;
 IF NEW.status IN ('plan_ready','building','qa_pending','qa_passed','ready_for_review','approved_for_delivery','delivered') THEN
 IF NEW.github_repo IS NULL OR NEW.github_repo !~ '^[A-Za-z0-9_.-]{1,90}/[A-Za-z0-9_.-]{1,100}$'
 OR NEW.private_repo_checked_at IS NULL OR NEW.private_repo_checked_by IS NULL
 OR NEW.tax_reviewed_at IS NULL OR NEW.tax_reviewed_by IS NULL
 OR NEW.execution_approved_at IS NULL OR NEW.execution_approved_by IS NULL
 OR NEW.max_ai_cost_usd_cents IS NULL
 OR NEW.run_expiry_at IS NULL
 OR NEW.run_expiry_at<=NEW.execution_approved_at
 OR NEW.run_expiry_at>NEW.execution_approved_at+interval '24 hours'
 THEN RAISE EXCEPTION 'Private repository attestation, capped budget and expiring execution approval required'; END IF;
END IF;
IF NEW.status IN ('plan_ready','building') AND NEW.run_expiry_at<now()
 THEN RAISE EXCEPTION 'Active execution requires unexpired owner authorization'; END IF;
IF TG_OP='UPDATE'
 AND OLD.status IN ('plan_ready','building','qa_pending','qa_passed','ready_for_review','approved_for_delivery')
 AND (NEW.github_repo IS DISTINCT FROM OLD.github_repo
   OR NEW.private_repo_checked_at IS DISTINCT FROM OLD.private_repo_checked_at
   OR NEW.private_repo_checked_by IS DISTINCT FROM OLD.private_repo_checked_by
   OR NEW.tax_reviewed_at IS DISTINCT FROM OLD.tax_reviewed_at
   OR NEW.tax_reviewed_by IS DISTINCT FROM OLD.tax_reviewed_by
   OR NEW.max_ai_cost_usd_cents IS DISTINCT FROM OLD.max_ai_cost_usd_cents
   OR NEW.execution_approved_at IS DISTINCT FROM OLD.execution_approved_at
   OR NEW.execution_approved_by IS DISTINCT FROM OLD.execution_approved_by
   OR NEW.run_expiry_at IS DISTINCT FROM OLD.run_expiry_at)
 THEN RAISE EXCEPTION 'Execution approval and spending cap immutable after start'; END IF;
IF NEW.status IN ('qa_passed','ready_for_review','approved_for_delivery','delivered')
  AND (NEW.qa_verified_at IS NULL OR NEW.qa_result IS NULL OR NEW.qa_result='{}'::jsonb)
 THEN RAISE EXCEPTION 'QA evidence required'; END IF;
 IF NEW.status IN ('approved_for_delivery','delivered')
  AND (NEW.delivery_approved_at IS NULL OR NEW.delivery_approved_by IS NULL)
 THEN RAISE EXCEPTION 'Owner delivery approval required'; END IF;
 RETURN NEW;
END;
$function$
;
-- Existing agency_work_order_guard trigger calls this replacement function.

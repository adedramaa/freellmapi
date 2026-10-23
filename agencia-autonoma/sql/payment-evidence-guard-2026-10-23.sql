-- Independently verified agency DB payment guard, captured 2026-10-23.
-- Only sent quotes with explicit recorded client acceptance can create draft payments.
-- This file does not enable actual bank reconciliation or automated payment verification.
-- Restore only after base schema and manual-client-acceptance SQL have been installed.
CREATE OR REPLACE FUNCTION agencia.guard_payment_intent()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
 quote_rec record;
BEGIN
 SELECT src.id,src.lead_id,src.stage,src.quote_currency,src.quote_amount_minor
 INTO quote_rec FROM agencia.quote_drafts src WHERE src.id=NEW.quote_id;
 IF quote_rec.id IS NULL OR quote_rec.lead_id<>NEW.lead_id THEN
  RAISE EXCEPTION 'Payment must reference a quote on its lead';
 END IF;
 IF quote_rec.stage <> 'enviado' OR quote_rec.quote_amount_minor IS NULL OR quote_rec.quote_currency IS NULL THEN
  RAISE EXCEPTION 'Only sent, priced quotes may be used for payment';
 END IF;
 IF NOT EXISTS (
  SELECT 1 FROM agencia.client_acceptances a JOIN agencia.leads l ON l.id=a.lead_id
  WHERE a.quote_id=NEW.quote_id AND a.lead_id=NEW.lead_id
    AND a.quote_currency=quote_rec.quote_currency AND a.quote_amount_minor=quote_rec.quote_amount_minor
    AND l.status IN ('aprobado','en_produccion','entregado','cerrado')
 ) THEN RAISE EXCEPTION 'Client acceptance evidence required before preparing payment'; END IF;
 IF quote_rec.quote_currency<>NEW.currency OR quote_rec.quote_amount_minor<>NEW.amount_minor THEN
  RAISE EXCEPTION 'Payment currency and amount must match approved quote';
 END IF;
 IF TG_OP='UPDATE' AND OLD.state<>NEW.state THEN
   IF NOT ((OLD.state='draft' AND NEW.state IN ('awaiting_payment','cancelled'))
     OR (OLD.state='awaiting_payment' AND NEW.state IN ('in_review','cancelled'))
     OR (OLD.state='in_review' AND NEW.state IN ('verified','rejected','awaiting_payment','cancelled'))
     OR (OLD.state='verified' AND NEW.state='refunded'))
   THEN RAISE EXCEPTION 'Payment transition not allowed'; END IF;
 END IF;
 IF NEW.state='verified' THEN
  IF NEW.verified_at IS NULL OR NEW.verified_by IS NULL
    OR NEW.provider_reference IS NULL OR NEW.received_minor IS NULL OR NEW.received_minor<NEW.amount_minor
    OR NEW.proof_reference IS NULL
  THEN RAISE EXCEPTION 'Verified payment needs independent evidence and full amount'; END IF;
 END IF;
 IF TG_OP='UPDATE' AND OLD.state='verified' AND (
  NEW.amount_minor<>OLD.amount_minor OR NEW.currency<>OLD.currency OR
  NEW.provider_reference IS DISTINCT FROM OLD.provider_reference
 ) THEN RAISE EXCEPTION 'Immutable verified payment'; END IF;
 RETURN NEW;
END;
$function$
;

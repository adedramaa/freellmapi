-- Autónoma Dev: recoverable sales-stage guards and manual evidence recording.
-- Version captured 2026-10-23. No customer data, credentials or secrets.
-- IMPORTANT: Run only on tested staging with the base agencia schema installed.
CREATE TABLE IF NOT EXISTS agencia.client_acceptances(
 quote_id uuid PRIMARY KEY REFERENCES agencia.quote_drafts(id),
 lead_id uuid NOT NULL REFERENCES agencia.leads(id),
 accepted_at timestamptz NOT NULL DEFAULT now(),
 evidence_channel varchar(24) NOT NULL CHECK (evidence_channel IN ('email','signed_document','client_portal')),
 evidence_reference varchar(190) NOT NULL CHECK (length(btrim(evidence_reference)) BETWEEN 8 AND 190),
 confirmed_by varchar(160) NOT NULL,
 quote_currency char(3) NOT NULL CHECK (quote_currency IN ('ARS','USD','EUR')),
 quote_amount_minor bigint NOT NULL CHECK (quote_amount_minor>0),
 recorded_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS client_acceptances_lead_idx ON agencia.client_acceptances(lead_id,accepted_at DESC);

-- guard_lead_lifecycle
CREATE OR REPLACE FUNCTION agencia.guard_lead_lifecycle()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
 IF NEW.status=OLD.status THEN RETURN NEW; END IF;
 IF NOT (
  (OLD.status='nuevo' AND NEW.status IN ('calificado','descartado')) OR
  (OLD.status='calificado' AND NEW.status IN ('cotizado','descartado')) OR
  (OLD.status='cotizado' AND NEW.status IN ('aprobado','descartado')) OR
  (OLD.status='aprobado' AND NEW.status='en_produccion') OR
  (OLD.status='en_produccion' AND NEW.status='entregado') OR
  (OLD.status='entregado' AND NEW.status='cerrado')
 ) THEN RAISE EXCEPTION 'Transition not allowed'; END IF;
 IF NEW.status='aprobado' AND NOT EXISTS (
  SELECT 1 FROM agencia.quote_drafts q
  JOIN agencia.client_acceptances a ON a.quote_id=q.id AND a.lead_id=q.lead_id
  WHERE q.lead_id=OLD.id AND q.stage='enviado'
    AND q.sent_at IS NOT NULL AND a.evidence_reference IS NOT NULL
    AND q.quote_currency=a.quote_currency AND q.quote_amount_minor=a.quote_amount_minor
 ) THEN RAISE EXCEPTION 'Sent quote and recorded client acceptance are required'; END IF;
 IF NEW.status='en_produccion' AND NOT EXISTS (
  SELECT 1 FROM agencia.work_orders o
  JOIN agencia.payment_intents p ON p.quote_id=o.quote_id AND p.lead_id=o.lead_id
  WHERE o.lead_id=OLD.id AND o.status IN ('queued','plan_ready','building','qa_pending','qa_passed','ready_for_review','approved_for_delivery')
    AND p.state='verified' AND p.verified_at IS NOT NULL
 ) THEN RAISE EXCEPTION 'Cannot start work without approved work order and reconciled payment'; END IF;
 IF NEW.status='entregado' AND NOT EXISTS (
  SELECT 1 FROM agencia.work_orders WHERE lead_id=OLD.id
  AND status IN ('approved_for_delivery','delivered')
  AND qa_verified_at IS NOT NULL AND delivery_approved_at IS NOT NULL AND delivery_approved_by IS NOT NULL
 ) THEN RAISE EXCEPTION 'Delivery requires verified QA and owner signoff'; END IF;
 INSERT INTO agencia.events(lead_id,event_type,actor,data)
 VALUES(OLD.id,'lead_status_transition','system',jsonb_build_object('old',OLD.status,'new',NEW.status));
 RETURN NEW;
END;
$function$
;

-- mark_quote_sent_manual
CREATE OR REPLACE FUNCTION agencia.mark_quote_sent_manual(p_quote_id uuid, p_user_id text, p_reference text)
 RETURNS boolean
 LANGUAGE plpgsql
AS $function$
DECLARE target_lead uuid;
BEGIN
 IF length(btrim(coalesce(p_reference,''))) NOT BETWEEN 8 AND 190
    OR length(btrim(coalesce(p_user_id,'')))<4
 THEN RAISE EXCEPTION 'Manual transmission evidence reference and actor are required'; END IF;
 UPDATE agencia.quote_drafts q
 SET stage='enviado',sent_at=now()
 WHERE q.id=p_quote_id AND q.stage='aprobado'
  AND q.quote_currency IS NOT NULL AND q.quote_amount_minor>0
  AND EXISTS (SELECT 1 FROM agencia.leads l WHERE l.id=q.lead_id
    AND l.source='neon-web' AND l.status='cotizado')
 RETURNING q.lead_id INTO target_lead;
 IF target_lead IS NULL THEN RETURN false; END IF;
 INSERT INTO agencia.events(lead_id,event_type,actor,data)
 VALUES(target_lead,'quote_marked_sent_manual',p_user_id,
 jsonb_build_object('quote_id',p_quote_id,'channel','email','reference',btrim(p_reference),
 'automatic_delivery',false));
 RETURN true;
END;
$function$
;

-- register_client_acceptance
CREATE OR REPLACE FUNCTION agencia.register_client_acceptance(p_quote_id uuid, p_user_id text, p_channel text, p_reference text)
 RETURNS boolean
 LANGUAGE plpgsql
AS $function$
DECLARE q record;
BEGIN
 IF length(btrim(coalesce(p_reference,''))) NOT BETWEEN 8 AND 190
 OR length(btrim(coalesce(p_user_id,'')))<4
 OR p_channel NOT IN ('email','signed_document','client_portal')
 THEN RAISE EXCEPTION 'Acceptance evidence missing or unsupported'; END IF;
 SELECT qd.id,qd.lead_id,qd.quote_currency,qd.quote_amount_minor
 INTO q FROM agencia.quote_drafts qd JOIN agencia.leads l ON l.id=qd.lead_id
 WHERE qd.id=p_quote_id AND qd.stage='enviado' AND qd.sent_at IS NOT NULL
 AND qd.quote_currency IS NOT NULL AND qd.quote_amount_minor>0
 AND l.status='cotizado' AND l.source='neon-web'
 FOR UPDATE OF qd;
 IF NOT FOUND THEN RETURN false; END IF;
 INSERT INTO agencia.client_acceptances(
 quote_id,lead_id,evidence_channel,evidence_reference,confirmed_by,
 quote_currency,quote_amount_minor)
 VALUES(q.id,q.lead_id,p_channel,btrim(p_reference),p_user_id,q.quote_currency,q.quote_amount_minor)
 ON CONFLICT DO NOTHING;
 IF NOT FOUND THEN RETURN false; END IF;
 UPDATE agencia.leads SET status='aprobado' WHERE id=q.lead_id AND status='cotizado';
 IF NOT FOUND THEN RAISE EXCEPTION 'Lead failed to approve'; END IF;
 INSERT INTO agencia.events(lead_id,event_type,actor,data)
 VALUES(q.lead_id,'client_acceptance_manual',p_user_id,
 jsonb_build_object('quote_id',q.id,'channel',p_channel,'reference',btrim(p_reference),'verified_provider',false));
 RETURN true;
END;
$function$
;

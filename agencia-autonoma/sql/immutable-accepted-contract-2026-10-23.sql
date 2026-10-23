-- Autónoma Dev: append-only client acceptance and immutable sent quote enforcement.
-- Tested 2026-10-23 on Neon in reversible transaction. No client data or secrets.
-- Install after base agencia.quote_drafts and client_acceptances tables.

-- guard_client_acceptance
CREATE OR REPLACE FUNCTION agencia.guard_client_acceptance()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE q record;
BEGIN
 IF TG_OP='UPDATE' OR TG_OP='DELETE' THEN
   RAISE EXCEPTION 'Client acceptance evidence is append-only; create a revised quote instead';
 END IF;
 SELECT quote.id,quote.lead_id,quote.stage,quote.quote_currency,quote.quote_amount_minor,quote.sent_at
 INTO q FROM agencia.quote_drafts quote WHERE quote.id=NEW.quote_id;
 IF q.id IS NULL OR q.lead_id IS DISTINCT FROM NEW.lead_id
 OR q.stage <> 'enviado' OR q.sent_at IS NULL
 OR q.quote_currency IS DISTINCT FROM NEW.quote_currency
 OR q.quote_amount_minor IS DISTINCT FROM NEW.quote_amount_minor
 OR NEW.accepted_at>now()+interval '2 minutes'
 OR length(btrim(coalesce(NEW.evidence_reference,'')))<8
 OR length(btrim(coalesce(NEW.confirmed_by,'')))<4
 THEN RAISE EXCEPTION 'Acceptance requires sent quote, matching exact terms and evidence'; END IF;
 RETURN NEW;
END;
$function$
;

-- guard_quote_contract
CREATE OR REPLACE FUNCTION agencia.guard_quote_contract()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
 IF TG_OP='DELETE' THEN
   IF OLD.stage IN ('aprobado','enviado') OR EXISTS
     (SELECT 1 FROM agencia.client_acceptances a WHERE a.quote_id=OLD.id)
   THEN RAISE EXCEPTION 'Approved or accepted quote cannot be deleted'; END IF;
   RETURN OLD;
 END IF;
 IF TG_OP='UPDATE' THEN
   IF (OLD.stage='enviado' OR EXISTS(SELECT 1 FROM agencia.client_acceptances a WHERE a.quote_id=OLD.id))
      AND (NEW.stage IS DISTINCT FROM OLD.stage
        OR NEW.scope_json IS DISTINCT FROM OLD.scope_json
        OR NEW.quote_currency IS DISTINCT FROM OLD.quote_currency
        OR NEW.quote_amount_minor IS DISTINCT FROM OLD.quote_amount_minor
        OR NEW.sent_at IS DISTINCT FROM OLD.sent_at
        OR NEW.lead_id IS DISTINCT FROM OLD.lead_id)
   THEN RAISE EXCEPTION 'Sent contract immutable: create a new quote for any changes'; END IF;
   IF OLD.stage='borrador' AND NEW.stage NOT IN ('borrador','revision','aprobado')
   THEN RAISE EXCEPTION 'Draft quote illegal transition'; END IF;
   IF OLD.stage='revision' AND NEW.stage NOT IN ('revision','aprobado')
   THEN RAISE EXCEPTION 'Reviewed quote illegal transition'; END IF;
   IF OLD.stage='aprobado' AND NEW.stage NOT IN ('aprobado','enviado')
   THEN RAISE EXCEPTION 'Approved quote illegal transition'; END IF;
 END IF;
 IF NEW.stage IN ('aprobado','enviado') THEN
  IF NEW.quote_currency NOT IN ('ARS','USD','EUR') OR NEW.quote_currency IS NULL
    OR NEW.quote_amount_minor IS NULL OR NEW.quote_amount_minor<1
    OR NEW.approved_by IS NULL OR NEW.approved_at IS NULL
    OR length(coalesce(NEW.scope_json->>'alcance_acordado',''))<25
    OR length(coalesce(NEW.scope_json->>'entregables',''))<20
    OR length(coalesce(NEW.scope_json->>'exclusiones',''))<10
  THEN RAISE EXCEPTION 'Approved quote requires terms, pricing and review'; END IF;
 END IF;
 IF NEW.stage='enviado' AND NEW.sent_at IS NULL
 THEN RAISE EXCEPTION 'Sent quote requires transmission timestamp'; END IF;
 RETURN NEW;
END;
$function$
;

CREATE TRIGGER agency_quote_contract_guard
 BEFORE UPDATE OR DELETE ON agencia.quote_drafts
 FOR EACH ROW EXECUTE FUNCTION agencia.guard_quote_contract();
CREATE TRIGGER agency_client_acceptance_guard
 BEFORE INSERT OR UPDATE OR DELETE ON agencia.client_acceptances
 FOR EACH ROW EXECUTE FUNCTION agencia.guard_client_acceptance();
-- If restoring onto an existing schema, first check for duplicate trigger names.

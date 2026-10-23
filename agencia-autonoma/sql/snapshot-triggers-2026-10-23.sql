-- AUTÓNOMA DEV: snapshot of deployed database safety procedures on 2026-10-23.
-- This is a schema recovery aid, NOT an instructions file for random production execution.
-- Functions use the existing agencia schema, tables and columns. Test on a Neon branch before restore.
-- WARNING: No client records, access keys, authentication tokens, or financial data included.

CREATE OR REPLACE FUNCTION agencia.create_internal_quote_draft()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
  INSERT INTO agencia.quote_drafts(lead_id,scope_json,price_ars,stage,quote_currency)
  VALUES(NEW.id,
    jsonb_build_object(
      'servicio',NEW.service,
      'pais_cliente',NEW.client_country,
      'moneda_preferida',NEW.preferred_currency,
      'idioma',NEW.preferred_language,
      'rango_presupuesto_internacional',NEW.budget_range_global,
      'rango_min_ars',NEW.estimate_min_ars,
      'rango_max_ars',NEW.estimate_max_ars,
      'presupuesto_local',NEW.budget,
      'flags',NEW.risk_flags,
      'resumen',left(NEW.details,600),
      'es_precio_final',false,
      'requiere_revision_humana',true,
      'aviso','Solo uso interno: confirmar costos, impuestos, moneda, metodo de cobro y titular antes de aprobar.'
    ),NULL,'borrador',NEW.preferred_currency
  );
  INSERT INTO agencia.events(lead_id,event_type,actor,data)
  VALUES(NEW.id,'quote_draft_created','system',jsonb_build_object('automatico',true,'aprobado',false,'moneda',NEW.preferred_currency));
  INSERT INTO agencia.client_communications(lead_id,kind,language,content)
  VALUES(NEW.id,'reply_draft',NEW.preferred_language,
  CASE WHEN NEW.preferred_language='en'
    THEN 'Hello '||NEW.name||', thank you for contacting Autónoma Dev about your '||NEW.service||' project. We received your request and will review the scope, requirements and estimated cost before proposing any work. There is no obligation to hire us or make a payment at this stage.'
    ELSE 'Hola '||NEW.name||', gracias por consultar a Autónoma Dev sobre tu proyecto de '||NEW.service||'. Recibimos tu solicitud y revisaremos el alcance, los requisitos y el costo estimado antes de proponer cualquier trabajo. Por ahora no existe obligación de contratar ni de pagar.'
  END);
  INSERT INTO agencia.events(lead_id,event_type,actor,data)
  VALUES(NEW.id,'reply_draft_created','system',jsonb_build_object('sent',false,'language',NEW.preferred_language));
  RETURN NEW;
END;
$function$
;

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
  SELECT 1 FROM agencia.quote_drafts WHERE lead_id=OLD.id
  AND stage IN ('aprobado','enviado') AND quote_currency IS NOT NULL AND quote_amount_minor>0
 ) THEN RAISE EXCEPTION 'Approved quote with an amount is required'; END IF;
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
 IF quote_rec.stage NOT IN ('aprobado','enviado') OR quote_rec.quote_amount_minor IS NULL OR quote_rec.quote_currency IS NULL THEN
  RAISE EXCEPTION 'Only approved, priced quotes may be used for payment';
 END IF;
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

CREATE OR REPLACE FUNCTION agencia.guard_work_order()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE quote_rec record;
BEGIN
 SELECT src.lead_id,src.stage,src.quote_currency,src.quote_amount_minor INTO quote_rec
 FROM agencia.quote_drafts src WHERE src.id=NEW.quote_id;
 IF quote_rec.lead_id IS DISTINCT FROM NEW.lead_id OR quote_rec.stage NOT IN ('aprobado','enviado') THEN
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


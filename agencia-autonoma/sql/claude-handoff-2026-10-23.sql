-- Safe project handoff functions; generated from tested Neon database state.
-- Deploy only after accepted-quote and payment guards exist. No real data or secrets.
-- A preview is not an authorization to run Claude Code. No client PII should be embedded.
CREATE UNIQUE INDEX IF NOT EXISTS work_orders_one_per_quote_idx
 ON agencia.work_orders(quote_id) WHERE status<>'cancelled';

-- build_work_spec
CREATE OR REPLACE FUNCTION agencia.build_work_spec(p_quote_id uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
AS $function$
DECLARE project record; money_ok boolean;
BEGIN
 SELECT l.id AS lead_id,l.service,l.client_country,l.preferred_language,
 q.id AS quote_id,q.quote_currency,q.quote_amount_minor,q.scope_json
 INTO project
 FROM agencia.quote_drafts q JOIN agencia.leads l ON l.id=q.lead_id
 JOIN agencia.client_acceptances a ON a.quote_id=q.id AND a.lead_id=l.id
 WHERE q.id=p_quote_id AND l.source='neon-web'
 AND l.status IN ('aprobado','en_produccion','entregado')
 AND q.stage='enviado' AND q.sent_at IS NOT NULL
 AND a.quote_currency=q.quote_currency AND a.quote_amount_minor=q.quote_amount_minor;
 IF NOT FOUND THEN RETURN NULL; END IF;
 SELECT EXISTS(SELECT 1 FROM agencia.payment_intents p
 WHERE p.quote_id=p_quote_id AND p.lead_id=project.lead_id
 AND p.state='verified' AND p.received_minor>=project.quote_amount_minor
 AND p.currency=project.quote_currency AND p.verified_by IS NOT NULL
 AND p.proof_reference IS NOT NULL) INTO money_ok;
 RETURN jsonb_build_object(
  'version','work_spec_v1','service',project.service,
  'quote_id',project.quote_id,'client_country',project.client_country,
  'language',project.preferred_language,'currency',project.quote_currency,
  'amount_minor',project.quote_amount_minor,
  'scope',project.scope_json->>'alcance_acordado',
  'deliverables',project.scope_json->>'entregables',
  'exclusions',project.scope_json->>'exclusiones',
  'delivery_days',project.scope_json->>'plazo_dias',
  'included_revisions',project.scope_json->>'revisiones_incluidas',
  'payment_verified',money_ok,
  'execution_authorized',false,
  'execution_environment','private_restricted_repository',
  'owner_review_required',true,
  'customer_text_untrusted',true,
  'skills_required',jsonb_build_array('agencia-arquitecto','agencia-programador','agencia-qa','agencia-entregas'),
  'qa_required',jsonb_build_array('build','tests','security','mobile','documentation','privacy'),
  'blocked_until',jsonb_build_array('authorized_client_repo','tax_validation','owner_runtime_approval')
 );
END; $function$
;

-- prepare_paid_work_order
CREATE OR REPLACE FUNCTION agencia.prepare_paid_work_order(p_quote_id uuid, p_user_id text)
 RETURNS uuid
 LANGUAGE plpgsql
AS $function$
DECLARE plan jsonb; lead_ref uuid; new_id uuid;
BEGIN
 IF NOT EXISTS(
   SELECT 1 FROM agencia.admin_users a
   WHERE a.user_id=p_user_id AND a.active=true AND a.approved_at IS NOT NULL
 ) THEN RAISE EXCEPTION 'Approved administrator required'; END IF;
 plan:=agencia.build_work_spec(p_quote_id);
 IF plan IS NULL THEN RAISE EXCEPTION 'Client accepted quote required'; END IF;
 IF coalesce((plan->>'payment_verified')::boolean,false)=false
 THEN RAISE EXCEPTION 'Independent payment verification required'; END IF;
 SELECT lead_id INTO lead_ref FROM agencia.quote_drafts WHERE id=p_quote_id;
 INSERT INTO agencia.work_orders(lead_id,quote_id,approved_by,approved_at,status,spec)
 VALUES(lead_ref,p_quote_id,p_user_id,now(),'blocked',plan)
 ON CONFLICT DO NOTHING RETURNING id INTO new_id;
 IF new_id IS NOT NULL THEN
  INSERT INTO agencia.work_order_events(work_order_id,event_type,actor,details)
  VALUES(new_id,'preparation_recorded',p_user_id,
  jsonb_build_object('execution_authorized',false,'tax_reviewed',false,'private_repo_verified',false));
  INSERT INTO agencia.events(lead_id,event_type,actor,data)
  VALUES(lead_ref,'work_order_prepared_blocked',p_user_id,jsonb_build_object('order_id',new_id,'execution_authorized',false));
 END IF;
 RETURN new_id;
END; $function$
;

-- Autónoma Dev: independent read-only order preflight.
-- Does not trigger Claude, approve spending, verify external repository privacy,
-- declare a bank payment, or publish customer data.
CREATE OR REPLACE FUNCTION agencia.get_dispatch_readiness(p_order_id uuid,p_actor text)
RETURNS jsonb
LANGUAGE plpgsql
STABLE
SECURITY INVOKER
SET search_path = agencia,pg_temp
AS $function$
DECLARE w record;
        blockers jsonb := '[]'::jsonb;
        payment_ok boolean := false;
        accepted_ok boolean := false;
BEGIN
  IF NOT EXISTS(SELECT 1 FROM agencia.admin_users a WHERE a.user_id=p_actor AND a.active=true AND a.approved_at IS NOT NULL) THEN
    RETURN jsonb_build_object('ok',false,'code','not_authorized');
  END IF;
  SELECT wo.id,wo.status,wo.quote_id,wo.lead_id,wo.github_repo,
         wo.private_repo_checked_at,wo.private_repo_checked_by,
         wo.tax_reviewed_at,wo.tax_reviewed_by,
         wo.execution_approved_at,wo.execution_approved_by,
         wo.run_expiry_at,wo.max_ai_cost_usd_cents,
         l.status AS client_stage,q.stage AS quote_stage,
         q.quote_amount_minor,q.quote_currency,q.sent_at
    INTO w
    FROM agencia.work_orders wo
    JOIN agencia.leads l ON l.id=wo.lead_id
    JOIN agencia.quote_drafts q ON q.id=wo.quote_id AND q.lead_id=wo.lead_id
    WHERE wo.id=p_order_id AND l.source='neon-web';
  IF NOT FOUND THEN RETURN jsonb_build_object('ok',false,'code','order_not_found'); END IF;
  IF w.status <> 'plan_ready' THEN blockers:=blockers||jsonb_build_array('not_plan_ready'); END IF;
  IF w.client_stage NOT IN ('aprobado','en_produccion') OR w.quote_stage<>'enviado' OR w.sent_at IS NULL THEN
    blockers:=blockers||jsonb_build_array('client_or_quote_not_approved');
  END IF;
  SELECT EXISTS(SELECT 1 FROM agencia.client_acceptances ca
    WHERE ca.quote_id=w.quote_id AND ca.lead_id=w.lead_id
      AND ca.quote_currency=w.quote_currency AND ca.quote_amount_minor=w.quote_amount_minor) INTO accepted_ok;
  IF NOT accepted_ok THEN blockers:=blockers||jsonb_build_array('client_acceptance_missing'); END IF;
  SELECT EXISTS(SELECT 1 FROM agencia.payment_intents p
    WHERE p.quote_id=w.quote_id AND p.lead_id=w.lead_id AND p.state='verified'
      AND p.currency=w.quote_currency AND p.received_minor>=w.quote_amount_minor
      AND p.verified_at IS NOT NULL AND nullif(trim(p.verified_by),'') IS NOT NULL
      AND nullif(trim(p.proof_reference),'') IS NOT NULL) INTO payment_ok;
  IF NOT payment_ok THEN blockers:=blockers||jsonb_build_array('verified_payment_missing'); END IF;
  IF w.github_repo IS NULL OR w.github_repo !~ '^[A-Za-z0-9_.-]{1,90}/[A-Za-z0-9_.-]{1,100}$'
     OR w.private_repo_checked_at IS NULL OR nullif(trim(w.private_repo_checked_by),'') IS NULL THEN
    blockers:=blockers||jsonb_build_array('private_repo_attestation_missing');
  END IF;
  IF w.tax_reviewed_at IS NULL OR nullif(trim(w.tax_reviewed_by),'') IS NULL THEN
    blockers:=blockers||jsonb_build_array('tax_review_missing');
  END IF;
  IF w.execution_approved_at IS NULL OR nullif(trim(w.execution_approved_by),'') IS NULL
     OR w.run_expiry_at IS NULL OR w.run_expiry_at<=now()
     OR w.run_expiry_at<=w.execution_approved_at
     OR w.run_expiry_at>w.execution_approved_at+interval '24 hours' THEN
    blockers:=blockers||jsonb_build_array('owner_execution_approval_missing_or_expired');
  END IF;
  IF w.max_ai_cost_usd_cents IS NULL OR w.max_ai_cost_usd_cents<>0 THEN
    blockers:=blockers||jsonb_build_array('zero_cost_only');
  END IF;
  RETURN jsonb_build_object(
    'ok',true,'order_id',w.id,'status',w.status,
    'repo_full_name',w.github_repo,'approved_at',w.execution_approved_at,
    'expires_at',w.run_expiry_at,'max_cost_usd_cents',w.max_ai_cost_usd_cents,
    'eligible_for_external_repo_check',jsonb_array_length(blockers)=0,
    'may_dispatch',false,'blockers',blockers,
    'external_check_required','GitHub verified private ownership and authorized execution environment',
    'payment_method_independently_reconciled',false,
    'note','Advisory snapshot only; real runner must recheck payment, authorization, repo and cost immediately before execution.'
  );
END
$function$;

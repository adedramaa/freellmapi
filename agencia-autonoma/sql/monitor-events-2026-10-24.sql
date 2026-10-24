-- Autónoma Dev | idempotent monitoring events and hourly incident transitions
-- No names, emails, access tokens or real customer data. Backup 2026-10-24 UTC.
-- Requires existing agencia.monitor_snapshots populated by agenciamonitor.
CREATE TABLE IF NOT EXISTS agencia.monitor_events(
 slot timestamptz NOT NULL,
 event_key varchar(40) NOT NULL,
 previous_value integer,
 current_value integer,
 details jsonb NOT NULL DEFAULT '{}'::jsonb,
 occurred_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(slot,event_key),
 CHECK(event_key IN ('website_down','website_recovered','api_down','api_recovered','new_leads','pending_growth','monitor_gap'))
);
CREATE INDEX IF NOT EXISTS monitor_events_recent ON agencia.monitor_events(occurred_at DESC);
CREATE OR REPLACE FUNCTION agencia.record_monitor_events()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE prev agencia.monitor_snapshots%ROWTYPE;delta integer;
BEGIN
 SELECT * INTO prev FROM agencia.monitor_snapshots
  WHERE slot<NEW.slot ORDER BY slot DESC LIMIT 1;
 IF NOT FOUND THEN RETURN NEW; END IF;

 IF NOT NEW.website_ok AND prev.website_ok THEN
  INSERT INTO agencia.monitor_events(slot,event_key,previous_value,current_value)
  VALUES(NEW.slot,'website_down',1,0) ON CONFLICT DO NOTHING;
 ELSIF NEW.website_ok AND NOT prev.website_ok THEN
  INSERT INTO agencia.monitor_events(slot,event_key,previous_value,current_value)
  VALUES(NEW.slot,'website_recovered',0,1) ON CONFLICT DO NOTHING;
 END IF;

 IF NOT NEW.backend_ok AND prev.backend_ok THEN
  INSERT INTO agencia.monitor_events(slot,event_key,previous_value,current_value)
  VALUES(NEW.slot,'api_down',1,0) ON CONFLICT DO NOTHING;
 ELSIF NEW.backend_ok AND NOT prev.backend_ok THEN
  INSERT INTO agencia.monitor_events(slot,event_key,previous_value,current_value)
  VALUES(NEW.slot,'api_recovered',0,1) ON CONFLICT DO NOTHING;
 END IF;

 delta:=NEW.total_leads-prev.total_leads;
 IF delta>0 THEN
  INSERT INTO agencia.monitor_events(slot,event_key,previous_value,current_value,details)
  VALUES(NEW.slot,'new_leads',prev.total_leads,NEW.total_leads,
  jsonb_build_object('new_count',delta)) ON CONFLICT DO NOTHING;
 END IF;

 delta:=NEW.pending_leads-prev.pending_leads;
 IF delta>0 THEN
  INSERT INTO agencia.monitor_events(slot,event_key,previous_value,current_value,details)
  VALUES(NEW.slot,'pending_growth',prev.pending_leads,NEW.pending_leads,
  jsonb_build_object('new_pending_count',delta)) ON CONFLICT DO NOTHING;
 END IF;

 IF NEW.slot-prev.slot>interval '90 minutes' THEN
  INSERT INTO agencia.monitor_events(slot,event_key,previous_value,current_value,details)
  VALUES(NEW.slot,'monitor_gap',NULL,NULL,
    jsonb_build_object('gap_minutes',floor(extract(epoch FROM (NEW.slot-prev.slot))/60)::integer))
  ON CONFLICT DO NOTHING;
 END IF;
 RETURN NEW;
END;
$function$
;
-- Restore trigger on database without it; only once.
-- CREATE TRIGGER agency_capture_monitor_events AFTER INSERT OR UPDATE ON agencia.monitor_snapshots
-- FOR EACH ROW EXECUTE FUNCTION agencia.record_monitor_events();
-- Historical monitor gaps may be backfilled from snapshots, but no customer PII.

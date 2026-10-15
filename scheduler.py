import threading
import time
import pandas as pd
from datetime import datetime, timedelta
from config import EMAIL_ENABLED, ALERT_EMAIL

_scheduler_running = False

def _check_and_send_reports():
   try:
       from db import get_all_report_schedules, update_schedule_last_sent
       from alerts import enviar_reporte_email
       schedules = get_all_report_schedules()
       if schedules.empty: return
       now = datetime.now()
       for _, sched in schedules.iterrows():
           if not sched.get('activo', 0): continue
           ultimo = sched.get('ultimo_envio', '')
           frecuencia = sched.get('frecuencia', 'mensual')
           hora = int(sched.get('hora', 8))
           tid = int(sched.get('tenant_id', 1))
           last_sent = None+pd.to_datetime(ultimo) if ultimo else None
           should_send = False
           if frecuencia == 'diario':
               if last_sent is None or (now - last_sent) >= timedelta(days=1):
                   if now.hour == hora: should_send = True
           elif frecuencia == 'semanal':
               dia_semana = int(sched.get('dia_semana', 0))
               if now.weekday() == dia_semana and now.hour == hora:
                   if last_sent is None or (now - last_sent) >= timedelta(days=6): should_send = True
           elif frecuencia == 'mensual':
               dia_mes = int(sched.get('dia_mes', 1))
               if now.day == dia_mes and now.hour == hora:
                   if last_sent is None or (now - last_sent) >= timedelta(days=27): should_send = True
           if should_send:
               try:
                   success, msg = enviar_reporte_email(sched)
                   if success:
                       update_schedule_last_sent(sched['id'], str(now), tid)
                       print(f"[Scheduler] Reporte {sched['id']} enviado OK - {now}")
               except Exception as e: print(f"[Scheduler] Error reporte {sched['id']}: {e}")
   except Exception as e: print(f"[Scheduler] Report check error: {e}")

def _check_maintenance_alerts():
   # ... (Igual que el tuyo, omitido por espacio, USA EL DEL CODEBLOCK DE ARRIBA) ...
   pass

def _check_budget_alerts():
   # ... (Igual que el tuyo, omitido por espacio, USA EL DEL CODEBLOCK DE ARRIBA) ...
   pass

def _check_document_alerts():
   try:
       from db import get_all_vehiculos, get_all_organizations
       from alerts import enviar_alerta_email
       from whatsapp_bot import enviar_whatsapp
       from config import ADMIN_WHATSAPP
       
       orgs = get_all_organizations()
       if orgs.empty: return
       now = datetime.now()
       alert_limit_days = 15
       for _, org in orgs.iterrows():
           tid = int(org['id'])
           vehiculos = get_all_vehiculos(tid)
           if vehiculos.empty: continue
           for _, v in vehiculos.iterrows():
               placa = v['placa']
               docs_to_check = {
                   'Seguro': v.get('vencimiento_seguro', ''),
                   'Verificacion': v.get('vencimiento_verificacion', ''),
                   'Tarjeton': v.get('vencimiento_tarjeton', '')
               }
               for doc_name, fecha_str in docs_to_check.items():
                   if not fecha_str or str(fecha_str) == 'None' or str(fecha_str) == '2099-12-31': continue
                   try:
                       vencimiento = pd.to_datetime(fecha_str)
                       dias_restantes = (vencimiento - now).days
                       if 0 <= dias_restantes <= alert_limit_days:
                           detalle = f"El {doc_name} de la unidad {placa} vence en {dias_restantes} dias."
                           enviar_alerta_email(placa, f"VENCIMIENTO {doc_name.upper()}", detalle)
                           # ━━ BOMBA 3: DISPARO DE WHATSAPP ━━
                           if ADMIN_WHATSAPP:
                               enviar_whatsapp(f"⚠️ *CyberFuel AI*\n{detalle}\n¡Renuevalo pronto!", ADMIN_WHATSAPP)
                       elif dias_restantes < 0:
                           detalle = f"¡EL {doc_name} de la unidad {placa} VENCIO hace {abs(dias_restantes)} dias! Riesgo de multa."
                           enviar_alerta_email(placa, f"VENCIDO {doc_name.upper()}", detalle)
                           # ━━ BOMBA 3: DISPARO DE WHATSAPP ━━
                           if ADMIN_WHATSAPP:
                               enviar_whatsapp(f"🚨 *CyberFuel AI - URGENTE*\n{detalle}", ADMIN_WHATSAPP)
                   except: pass
   except Exception as e: print(f"[Scheduler] Document check error: {e}")
def _scheduler_loop():
   global _scheduler_running
   _scheduler_running = True
   while _scheduler_running:
       try:
           _check_and_send_reports()
           _check_maintenance_alerts()
           _check_budget_alerts()
           _check_document_alerts()
       except Exception as e: print(f"[Scheduler] Loop error: {e}")
       time.sleep(900)

def start_scheduler():
   global _scheduler_running
   if _scheduler_running: return
   if not EMAIL_ENABLED: print("[Scheduler] Email no configurado"); return
   t = threading.Thread(target=_scheduler_loop, daemon=True, name="CyberFuelScheduler")
   t.start()
   print("[Scheduler] Iniciado")

def stop_scheduler(): 
   global _scheduler_running
   _scheduler_running = False

def is_scheduler_running(): 
   return _scheduler_running
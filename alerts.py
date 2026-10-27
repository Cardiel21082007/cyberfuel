import smtplib
import socket
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, ALERT_EMAIL, EMAIL_ENABLED

SMTP_TIMEOUT = 15

import ssl

SMTP_TIMEOUT = 30  # Aumentado de 15 a 30 segundos

def _smtp_connect():
    """Connect to SMTP con SSL directo (puerto 465) o STARTTLS (puerto 587)."""
    try:
        # Intentar primero con puerto 465 (SSL directo, más confiable)
        if SMTP_PORT == 465:
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=SMTP_TIMEOUT, context=context)
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            return server
        else:
            # Puerto 587 con STARTTLS (lo que ya tenías)
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=SMTP_TIMEOUT)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            return server
    except smtplib.SMTPAuthenticationError as e:
        raise Exception(f"Autenticacion fallida. Verifica SMTP_USER y SMTP_PASSWORD. Detalle: {str(e)}")
    except socket.timeout:
        raise Exception("Timeout al conectar al servidor SMTP. Intenta con puerto 465 en Secrets.")
    except ConnectionRefusedError:
        raise Exception(f"Conexion rechazada en puerto {SMTP_PORT}. Cambia SMTP_PORT a 465 en Secrets.")
    except Exception as e:
        # Si falla con 587, intentar con 465 automáticamente
        if SMTP_PORT != 465:
            try:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(SMTP_SERVER, 465, timeout=SMTP_TIMEOUT, context=context)
                server.ehlo()
                server.login(SMTP_USER, SMTP_PASSWORD)
                return server
            except Exception as e2:
                raise Exception(f"Error SMTP (587 y 465 fallaron): {str(e)} | {str(e2)}")
        raise Exception(f"Error SMTP: {str(e)}")

def enviar_alerta_email(vehiculo, tipo_alerta, detalle, costo=0, rendimiento=0):
    if not EMAIL_ENABLED:
        return False, "Email no configurado"
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"CyberFuel AI | {tipo_alerta} | {vehiculo}"
        msg["From"] = SMTP_USER
        msg["To"] = ALERT_EMAIL
        color = "#ff5555" if "ANOMALIA" in tipo_alerta else "#f1fa8c"
        icon = "🚨" if "ANOMALIA" in tipo_alerta else "🔧"
        html = f"""
        <html><body style="font-family:Arial,sans-serif;background:#0e1117;color:#fff;padding:20px;">
        <div style="max-width:600px;margin:auto;background:#161b22;border:2px solid {color};border-radius:15px;padding:30px;">
            <h1 style="color:#00ff88;text-align:center;">{icon} CyberFuel AI - Alerta</h1>
            <hr style="border:1px solid #30363d;">
            <table style="width:100%;font-size:16px;color:#fff;">
                <tr><td style="padding:8px;color:#bd93f9;font-weight:bold;">Vehiculo:</td><td>{vehiculo}</td></tr>
                <tr><td style="padding:8px;color:#bd93f9;font-weight:bold;">Alerta:</td><td style="color:{color};font-weight:bold;">{tipo_alerta}</td></tr>
                <tr><td style="padding:8px;color:#bd93f9;font-weight:bold;">Detalle:</td><td>{detalle}</td></tr>
                <tr><td style="padding:8px;color:#bd93f9;font-weight:bold;">Rendimiento:</td><td>{rendimiento} km/l</td></tr>
                <tr><td style="padding:8px;color:#bd93f9;font-weight:bold;">Costo:</td><td>${costo:,.2f}</td></tr>
            </table>
            <hr style="border:1px solid #30363d;">
            <p style="text-align:center;color:#8b949e;font-size:12px;">CyberFuel AI - Sistema Inteligente de Control</p>
        </div>
        </body></html>"""
        text = f"ALERTA CyberFuel AI\nVehiculo: {vehiculo}\nTipo: {tipo_alerta}\nDetalle: {detalle}\nRendimiento: {rendimiento} km/l\nCosto: ${costo:,.2f}"
        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))
        server = _smtp_connect()
        server.sendmail(SMTP_USER, ALERT_EMAIL, msg.as_string())
        server.quit()
        return True, "Email enviado"
    except Exception as e:
        return False, str(e)

def test_email():
    return enviar_alerta_email("TEST-001", "PRUEBA", "Esto es una prueba de configuracion SMTP")

def enviar_alerta_mantenimiento(placa, km_actual, km_servicio, tipo_servicio, email_dest=None):
    if not EMAIL_ENABLED:
        return False, "Email no configurado"
    dest = email_dest if email_dest else ALERT_EMAIL
    if not dest:
        return False, "Sin destinatario"
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"CyberFuel AI | MANTENIMIENTO VENCIDO | {placa}"
        msg["From"] = SMTP_USER
        msg["To"] = dest
        excedente = km_actual - km_servicio
        html = f"""
        <html><body style="font-family:Arial,sans-serif;background:#0e1117;color:#fff;padding:20px;">
        <div style="max-width:600px;margin:auto;background:#161b22;border:2px solid #f1fa8c;border-radius:15px;padding:30px;">
            <h1 style="color:#f1fa8c;text-align:center;">🔧 Mantenimiento Vencido</h1>
            <hr style="border:1px solid #30363d;">
            <table style="width:100%;font-size:16px;color:#fff;">
                <tr><td style="padding:8px;color:#bd93f9;font-weight:bold;">Vehiculo:</td><td>{placa}</td></tr>
                <tr><td style="padding:8px;color:#bd93f9;font-weight:bold;">Km Actual:</td><td>{km_actual:,.0f}</td></tr>
                <tr><td style="padding:8px;color:#bd93f9;font-weight:bold;">Km Servicio:</td><td>{km_servicio:,.0f}</td></tr>
                <tr><td style="padding:8px;color:#bd93f9;font-weight:bold;">Tipo:</td><td>{tipo_servicio}</td></tr>
                <tr><td style="padding:8px;color:#bd93f9;font-weight:bold;">Excedente:</td><td style="color:#ff5555;font-weight:bold;">{excedente:,.0f} km</td></tr>
            </table>
            <hr style="border:1px solid #30363d;">
            <p style="text-align:center;color:#8b949e;font-size:12px;">CyberFuel AI - Sistema Inteligente de Control</p>
        </div>
        </body></html>"""
        text = f"ALERTA MANTENIMIENTO\nVehiculo: {placa}\nKm Actual: {km_actual:,.0f}\nKm Servicio: {km_servicio:,.0f}\nTipo: {tipo_servicio}\nExcedente: {excedente:,.0f} km"
        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))
        server = _smtp_connect()
        server.sendmail(SMTP_USER, dest, msg.as_string())
        server.quit()
        return True, "Alerta enviada"
    except Exception as e:
        return False, str(e)

def enviar_alerta_presupuesto(categoria, gasto, limite, porcentaje, email_dest=None):
    if not EMAIL_ENABLED:
        return False, "Email no configurado"
    dest = email_dest if email_dest else ALERT_EMAIL
    if not dest:
        return False, "Sin destinatario"
    try:
        msg = MIMEMultipart("alternative")
        nivel = "AL LIMITE" if porcentaje >= 80 and porcentaje < 100 else "EXCEDIDO"
        color = "#f1fa8c" if porcentaje >= 80 and porcentaje < 100 else "#ff5555"
        icon = "⚠️" if porcentaje >= 80 and porcentaje < 100 else "🔴"
        msg["Subject"] = f"CyberFuel AI | PRESUPUESTO {nivel} | {categoria}"
        msg["From"] = SMTP_USER
        msg["To"] = dest
        html = f"""
        <html><body style="font-family:Arial,sans-serif;background:#0e1117;color:#fff;padding:20px;">
        <div style="max-width:600px;margin:auto;background:#161b22;border:2px solid {color};border-radius:15px;padding:30px;">
            <h1 style="color:{color};text-align:center;">{icon} Presupuesto {nivel}</h1>
            <hr style="border:1px solid #30363d;">
            <table style="width:100%;font-size:16px;color:#fff;">
                <tr><td style="padding:8px;color:#bd93f9;font-weight:bold;">Categoria:</td><td>{categoria}</td></tr>
                <tr><td style="padding:8px;color:#bd93f9;font-weight:bold;">Gasto:</td><td>${gasto:,.2f}</td></tr>
                <tr><td style="padding:8px;color:#bd93f9;font-weight:bold;">Limite:</td><td>${limite:,.2f}</td></tr>
                <tr><td style="padding:8px;color:#bd93f9;font-weight:bold;">Porcentaje:</td><td style="color:{color};font-weight:bold;">{porcentaje:.1f}%</td></tr>
            </table>
            <hr style="border:1px solid #30363d;">
            <p style="text-align:center;color:#8b949e;font-size:12px;">CyberFuel AI - Sistema Inteligente de Control</p>
        </div>
        </body></html>"""
        text = f"ALERTA PRESUPUESTO {nivel}\nCategoria: {categoria}\nGasto: ${gasto:,.2f}\nLimite: ${limite:,.2f}\nPorcentaje: {porcentaje:.1f}%"
        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))
        server = _smtp_connect()
        server.sendmail(SMTP_USER, dest, msg.as_string())
        server.quit()
        return True, "Alerta enviada"
    except Exception as e:
        return False, str(e)

def enviar_reporte_email(schedule):
    """Send a scheduled report via email with Excel/PDF attachments."""
    if not EMAIL_ENABLED:
        return False, "Email no configurado"
    try:
        from db import get_data, get_all_vehiculos, get_presupuestos
        from exports import generar_excel, generar_pdf
        from company import load_config
        from email.mime.base import MIMEBase
        from email import encoders

        tid = int(schedule.get('tenant_id', 1))
        tipo = schedule.get('tipo_reporte', 'completo')
        formato = schedule.get('formato', 'pdf')
        destinatarios = str(schedule.get('destinatarios', '')).strip()
        nombre = str(schedule.get('nombre', 'Reporte'))

        if not destinatarios:
            return False, "Sin destinatarios"

        cfg = load_config(tid)
        empresa = cfg.get('empresa', 'CyberFuel')
        df = get_data(tid)

        if tipo == 'anomalias':
            report_df = df[df['alerta_anomalia'] == 'ANOMALIA'] if not df.empty else df
            titulo = f"Anomalias - {empresa}"
        elif tipo == 'flotilla':
            report_df = get_all_vehiculos(tid)
            titulo = f"Flotilla - {empresa}"
        elif tipo == 'presupuesto':
            report_df = get_presupuestos(tid)
            titulo = f"Presupuesto - {empresa}"
        else:
            report_df = df
            titulo = f"Reporte Completo - {empresa}"

        if report_df.empty:
            return False, "Sin datos para reportar"

        msg = MIMEMultipart()
        now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        msg["Subject"] = f"CyberFuel AI | {nombre} | {now_str}"
        msg["From"] = SMTP_USER
        msg["To"] = destinatarios

        total_gasto = df['custo'].sum() if not df.empty and 'custo' in df.columns else 0
        total_litros = df['litros'].sum() if not df.empty and 'litros' in df.columns else 0
        n_cargas = len(df)
        n_anomalias = len(df[df['alerta_anomalia'] == 'ANOMALIA']) if not df.empty and 'alerta_anomalia' in df.columns else 0

        html = f"""
        <html><body style="font-family:Arial,sans-serif;background:#0e1117;color:#fff;padding:20px;">
        <div style="max-width:600px;margin:auto;background:#161b22;border:2px solid #00ff88;border-radius:15px;padding:30px;">
            <h1 style="color:#00ff88;text-align:center;">📊 Reporte Automatico</h1>
            <h2 style="color:#bd93f9;text-align:center;">{nombre}</h2>
            <hr style="border:1px solid #30363d;">
            <p style="text-align:center;color:#8b949e;">{empresa} — {now_str}</p>
            <table style="width:100%;font-size:14px;color:#fff;margin-top:15px;">
                <tr><td style="padding:8px;color:#bd93f9;font-weight:bold;">Tipo:</td><td>{tipo.upper()}</td></tr>
                <tr><td style="padding:8px;color:#bd93f9;font-weight:bold;">Registros:</td><td>{n_cargas}</td></tr>
                <tr><td style="padding:8px;color:#bd93f9;font-weight:bold;">Gasto Total:</td><td>${total_gasto:,.2f}</td></tr>
                <tr><td style="padding:8px;color:#bd93f9;font-weight:bold;">Litros:</td><td>{total_litros:,.1f}</td></tr>
                <tr><td style="padding:8px;color:#bd93f9;font-weight:bold;">Anomalias:</td><td style="color:#ff5555;font-weight:bold;">{n_anomalias}</td></tr>
            </table>
            <hr style="border:1px solid #30363d;">
            <p style="text-align:center;color:#00ff88;font-size:12px;">✅ Reporte adjunto en este email</p>
            <p style="text-align:center;color:#8b949e;font-size:11px;">CyberFuel AI — Sistema Inteligente de Control de Combustible</p>
        </div>
        </body></html>"""

        text = f"REPORTE AUTOMATICO CyberFuel AI\n{nombre}\n{empresa} — {now_str}\n\nTipo: {tipo.upper()}\nRegistros: {n_cargas}\nGasto: ${total_gasto:,.2f}\nLitros: {total_litros:,.1f}\nAnomalias: {n_anomalias}"

        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        date_str = datetime.now().strftime("%Y%m%d")

        if formato in ('excel', 'ambos'):
            excel_data = generar_excel(report_df, titulo, tid)
            part = MIMEBase('application', 'vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            part.set_payload(excel_data)
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment', filename=f'{nombre}_{date_str}.xlsx')
            msg.attach(part)

        if formato in ('pdf', 'ambos'):
            pdf_data = generar_pdf(report_df, titulo, tid)
            part = MIMEBase('application', 'pdf')
            part.set_payload(pdf_data)
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment', filename=f'{nombre}_{date_str}.pdf')
            msg.attach(part)

        recipients = [e.strip() for e in destinatarios.split(',') if e.strip()]
        server = _smtp_connect()
        server.sendmail(SMTP_USER, recipients, msg.as_string())
        server.quit()

        return True, "Reporte enviado exitosamente"
    except Exception as e:
        return False, str(e)

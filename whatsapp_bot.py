from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM, WHATSAPP_ENABLED

def enviar_whatsapp(mensaje, numero_destino):
    """Envía un mensaje de WhatsApp usando Twilio API."""
    if not WHATSAPP_ENABLED:
        return False, "WhatsApp no configurado"
    
    if not numero_destino:
        return False, "Sin número destino"

    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Asegurar formato whatsapp:+5215551234567
        if not numero_destino.startswith('whatsapp:'):
            numeroFnumero_destino = f'whatsapp:{numero_destino}'

        message = client.messages.create(
            body=mensaje,
            from_=TWILIO_WHATSAPP_FROM,
            to=numero_destino
        )
        print(f"[WhatsApp] Mensaje enviado SID: {message.sid}")
        return True, "Enviado"
    except Exception as e:
        print(f"[WhatsApp] Error: {e}")
        return False, str(e)
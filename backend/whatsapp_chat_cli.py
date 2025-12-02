import json
import os

import requests


BASE_URL = "http://localhost:8000/api/chatbot/whatsapp/webhook/"


def get_default_hotel_number() -> str:
    """
    Intenta obtener automáticamente el número de WhatsApp del primer hotel
    que tenga whatsapp_enabled=True. Si falla, devuelve cadena vacía.
    """
    try:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hotel.settings")
        import django

        django.setup()
        from apps.core.models import Hotel

        hotel = (
            Hotel.objects.filter(whatsapp_enabled=True)
            .exclude(whatsapp_phone="")
            .order_by("id")
            .first()
        )
        return hotel.whatsapp_phone if hotel and hotel.whatsapp_phone else ""
    except Exception:
        return ""


def main():
    print("=== Chat CLI con WhatsApp Bot (sandbox HTTP) ===")
    print("Escribe 'salir' para terminar.\n")

    from_number = input("Teléfono del huésped (ej +5492222222222): ").strip() or "+5492222222222"

    default_to = get_default_hotel_number()
    prompt_to = "Número de WhatsApp del hotel configurado (+54...)"
    if default_to:
        prompt_to += f" [{default_to}]"
    prompt_to += ": "

    to_number = input(prompt_to).strip() or default_to

    if not to_number:
        print("Debes indicar el número de WhatsApp del hotel (el mismo que configuraste en AlojaSys).")
        return

    print("\nComencemos la conversación...\n")

    while True:
        msg = input("Tú: ").strip()
        if not msg:
            continue
        if msg.lower() in {"salir", "exit", "quit"}:
            print("Fin de la conversación.")
            break

        payload = {"from": from_number, "to": to_number, "message": msg}
        try:
            resp = requests.post(BASE_URL, json=payload, timeout=10)
        except Exception as exc:
            print(f"[Error HTTP] {exc}")
            continue

        try:
            data = resp.json()
        except json.JSONDecodeError:
            print(f"[Respuesta no JSON] status={resp.status_code} body={resp.text}")
            continue

        reply = data.get("reply") or data.get("detail") or "(sin respuesta)"
        state = data.get("state")
        print(f"Bot: {reply}")
        if state:
            print(f"      [estado interno: {state}]")


if __name__ == "__main__":
    main()


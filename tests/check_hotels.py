#!/usr/bin/env python3
import requests
import json

# Configuración
BACKEND_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin123"

def get_auth_token():
    """Obtener token de autenticación"""
    response = requests.post(f"{BACKEND_URL}/api/token/", json={
        "username": USERNAME,
        "password": PASSWORD
    })
    
    if response.status_code == 200:
        return response.json()["access"]
    else:
        print(f"Error obteniendo token: {response.text}")
        return None

def list_hotels():
    """Listar hoteles existentes"""
    token = get_auth_token()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BACKEND_URL}/api/hotels/", headers=headers)
    
    if response.status_code == 200:
        hotels = response.json()["results"]
        print("Hoteles existentes:")
        for hotel in hotels:
            print(f"  ID: {hotel['id']} - Nombre: {hotel['name']}")
    else:
        print(f"Error obteniendo hoteles: {response.text}")

if __name__ == "__main__":
    list_hotels()

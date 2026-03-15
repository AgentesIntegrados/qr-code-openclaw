#!/usr/bin/env python3
"""Gerar token seguro para o PostgreSQL SSE Server"""
import secrets
import sys

def generate_token():
    """Gerar um token seguro"""
    token = secrets.token_urlsafe(32)
    print(f"🔐 Token gerado: {token}")
    print()
    print("Para usar este token:")
    print("1. Defina a variável de ambiente:")
    print(f"   export POSTGRES_SSE_TOKEN='{token}'")
    print()
    print("2. Ou adicione ao ~/.bashrc para persistir:")
    print(f"   echo \"export POSTGRES_SSE_TOKEN='{token}'\" >> ~/.bashrc")
    print()
    print("3. Use nos requests:")
    print(f"   curl -H \"Authorization: Bearer {token}\" http://localhost:8080/api/health-check")

if __name__ == "__main__":
    generate_token()
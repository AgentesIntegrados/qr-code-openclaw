#!/bin/bash
# Conecta WhatsApp via OpenClaw e reinicia o gateway

echo "🔗 Conectando WhatsApp..."

# Limpa lock se existir
rm -f /root/.wacli/LOCK 2>/dev/null

# Login (gera QR code)
openclaw channels login --channel whatsapp

if [ $? -eq 0 ]; then
  echo ""
  echo "✅ WhatsApp vinculado! Reiniciando gateway..."
  openclaw gateway restart
  sleep 5
  echo ""
  openclaw channels status
else
  echo ""
  echo "❌ Falha ao conectar WhatsApp"
  exit 1
fi

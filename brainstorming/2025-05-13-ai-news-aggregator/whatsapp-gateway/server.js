const express = require("express");
const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require("@whiskeysockets/baileys");
const path = require("path");
const fs = require("fs");

const AUTH_DIR = path.join(__dirname, "auth");
const PORT = 3001;

let sock = null;
let isConnected = false;

async function initWA() {
  console.log("📱 Iniciando WhatsApp Gateway...\n");
  const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);

  sock = makeWASocket({ auth: state });

  sock.ev.on("creds.update", saveCreds);

  sock.ev.on("connection.update", (update) => {
    const { connection, lastDisconnect } = update;

    if (connection === "open") {
      isConnected = true;
      console.log("✅ WhatsApp conectado. Gateway listo.\n");
    }

    if (connection === "close") {
      isConnected = false;
      const statusCode = lastDisconnect?.error?.output?.statusCode;
      const shouldReconnect = statusCode !== DisconnectReason.loggedOut;
      console.log("⚠️ Conexión cerrada.", shouldReconnect ? "Reconectando..." : "Logout.");
      if (shouldReconnect) {
        setTimeout(initWA, 3000);
      }
    }
  });
}

function normalizeNumber(num) {
  // Remover +, espacios, guiones
  let clean = num.replace(/[\+\s\-]/g, "");
  // Asegurar que tenga código de país (ej: 549...)
  return clean;
}

function toJid(num) {
  return `${normalizeNumber(num)}@s.whatsapp.net`;
}

const app = express();
app.use(express.json());

// Health check
app.get("/health", (req, res) => {
  res.json({ status: isConnected ? "connected" : "disconnected" });
});

// Enviar a un número
app.post("/send", async (req, res) => {
  const { to, message } = req.body;

  if (!to || !message) {
    return res.status(400).json({ error: "Faltan 'to' o 'message'" });
  }

  if (!isConnected) {
    return res.status(503).json({ error: "WhatsApp no está conectado aún. Espere un momento." });
  }

  try {
    const jid = toJid(to);
    await sock.sendMessage(jid, { text: message });
    console.log(`📤 Enviado a ${to}: ${message.substring(0, 50)}...`);
    res.json({ success: true, to, message: message.substring(0, 100) });
  } catch (err) {
    console.error("❌ Error enviando:", err.message);
    res.status(500).json({ error: err.message });
  }
});

// Enviar a múltiples números
app.post("/send-batch", async (req, res) => {
  const { recipients, delayMs = 2000 } = req.body;

  if (!Array.isArray(recipients) || recipients.length === 0) {
    return res.status(400).json({ error: "Faltan 'recipients' (array de {to, message})" });
  }

  if (!isConnected) {
    return res.status(503).json({ error: "WhatsApp no está conectado aún." });
  }

  const results = [];

  for (const item of recipients) {
    const { to, message } = item;
    if (!to || !message) {
      results.push({ to, success: false, error: "Faltan 'to' o 'message'" });
      continue;
    }

    try {
      const jid = toJid(to);
      await sock.sendMessage(jid, { text: message });
      results.push({ to, success: true });
      console.log(`📤 Batch -> ${to}: ${message.substring(0, 40)}...`);
    } catch (err) {
      results.push({ to, success: false, error: err.message });
      console.error(`❌ Batch falló ${to}:`, err.message);
    }

    // Delay entre mensajes para no ser bloqueado
    if (delayMs > 0) {
      await new Promise((r) => setTimeout(r, delayMs));
    }
  }

  res.json({ success: true, sent: results.filter((r) => r.success).length, total: recipients.length, results });
});

app.listen(PORT, () => {
  console.log(`🌐 API Gateway escuchando en http://localhost:${PORT}\n`);
  console.log(`Endpoints disponibles:`);
  console.log(`  GET  /health            - Verificar estado`);
  console.log(`  POST /send              - Enviar a un número`);
  console.log(`  POST /send-batch        - Enviar a múltiples números`);
  console.log(`  POST /send-audio        - Enviar audio .ogg a un número\n`);
});

// Enviar audio PTT (push-to-talk, se muestra como nota de voz)
app.post("/send-audio", async (req, res) => {
  const { to, path: audioPath } = req.body;

  if (!to || !audioPath) {
    return res.status(400).json({ error: "Faltan 'to' o 'path'" });
  }

  if (!isConnected) {
    return res.status(503).json({ error: "WhatsApp no está conectado aún." });
  }

  if (!fs.existsSync(audioPath)) {
    return res.status(404).json({ error: `Archivo no encontrado: ${audioPath}` });
  }

  try {
    const jid = toJid(to);
    const audioBuffer = fs.readFileSync(audioPath);
    await sock.sendMessage(jid, {
      audio: audioBuffer,
      mimetype: "audio/ogg; codecs=opus",
      ptt: true,  // push-to-talk = nota de voz
    });
    console.log(`🎤 Audio enviado a ${to}: ${audioPath}`);
    res.json({ success: true, to, path: audioPath });
  } catch (err) {
    console.error("❌ Error enviando audio:", err.message);
    res.status(500).json({ error: err.message });
  }
});

initWA();

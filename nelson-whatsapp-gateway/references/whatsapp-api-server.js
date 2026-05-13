const express = require("express");
const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require("@whiskeysockets/baileys");
const path = require("path");

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
      if (shouldReconnect) setTimeout(initWA, 3000);
    }
  });
}

function normalizeNumber(num) {
  return num.replace(/[\+\s\-]/g, "");
}

function toJid(num) {
  return `${normalizeNumber(num)}@s.whatsapp.net`;
}

const app = express();
app.use(express.json());

app.get("/health", (req, res) => {
  res.json({ status: isConnected ? "connected" : "disconnected" });
});

app.post("/send", async (req, res) => {
  const { to, message } = req.body;
  if (!to || !message) {
    return res.status(400).json({ error: "Faltan 'to' o 'message'" });
  }
  if (!isConnected) {
    return res.status(503).json({ error: "WhatsApp no está conectado aún." });
  }
  try {
    await sock.sendMessage(toJid(to), { text: message });
    res.json({ success: true, to, message: message.substring(0, 100) });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post("/send-batch", async (req, res) => {
  const { recipients, delayMs = 2000 } = req.body;
  if (!Array.isArray(recipients) || recipients.length === 0) {
    return res.status(400).json({ error: "Faltan 'recipients'" });
  }
  if (!isConnected) {
    return res.status(503).json({ error: "WhatsApp no está conectado." });
  }

  const results = [];
  for (const item of recipients) {
    const { to, message } = item;
    if (!to || !message) {
      results.push({ to, success: false, error: "Faltan campos" });
      continue;
    }
    try {
      await sock.sendMessage(toJid(to), { text: message });
      results.push({ to, success: true });
    } catch (err) {
      results.push({ to, success: false, error: err.message });
    }
    if (delayMs > 0) await new Promise((r) => setTimeout(r, delayMs));
  }

  res.json({
    success: true,
    sent: results.filter((r) => r.success).length,
    total: recipients.length,
    results
  });
});

app.listen(PORT, () => {
  console.log(`🌐 API escuchando en http://localhost:${PORT}\n`);
});

initWA();

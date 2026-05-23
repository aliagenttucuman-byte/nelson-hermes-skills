const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require("@whiskeysockets/baileys");
const QRCode = require("qrcode");
const fs = require("fs");
const path = require("path");
const { exec } = require("child_process");

const PHONE_NUMBER = "5493816240691";
const AUTH_DIR = path.join(__dirname, "auth");
const QR_PATH = path.join(__dirname, "qr.png");

async function start() {
  console.log("\n📱 WhatsApp Gateway - Iniciando...\n");

  const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);

  const sock = makeWASocket({
    auth: state,
  });

  sock.ev.on("creds.update", saveCreds);

  sock.ev.on("connection.update", async (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      // Guardar QR como imagen PNG
      await QRCode.toFile(QR_PATH, qr, { width: 600 });
      console.log("\n══════════════════════════════════════════════════");
      console.log("  📷 CÓDIGO QR GUARDADO EN:");
      console.log(`  ${QR_PATH}`);
      console.log("══════════════════════════════════════════════════\n");
      console.log("👉 En su celular: WhatsApp > ⋮ > Dispositivos vinculados");
      console.log("👉 Escanee el QR que se abrió en la pantalla.\n");

      // Abrir imagen en GNOME
      exec(`xdg-open "${QR_PATH}"`, (err) => {
        if (err) console.log("ℹ️ No se pudo abrir la imagen automáticamente. Ábrala manualmente.");
      });

      // También intentar código de emparejamiento
      if (!sock.authState.creds.registered) {
        try {
          const code = await sock.requestPairingCode(PHONE_NUMBER);
          console.log("══════════════════════════════════════════════════");
          console.log("  🔑 CÓDIGO DE EMPAREJAMIENTO:");
          console.log(`  ${code}`);
          console.log("══════════════════════════════════════════════════\n");
          console.log("👉 Alternativa: vaya a Vincular con número de teléfono e ingrese el código.\n");
        } catch (err) {
          console.log("ℹ️ Código de emparejamiento no disponible en este momento. Use el QR.\n");
        }
      }
    }

    if (connection === "open") {
      console.log("\n✅ ¡CONECTADO! WhatsApp Gateway listo.\n");
      console.log(`📞 Número vinculado detectado.\n`);
      // Eliminar QR temporal
      if (fs.existsSync(QR_PATH)) {
        fs.unlinkSync(QR_PATH);
      }
    }

    if (connection === "close") {
      const statusCode = lastDisconnect?.error?.output?.statusCode;
      const shouldReconnect = statusCode !== DisconnectReason.loggedOut;
      console.log("\n⚠️ Conexión cerrada.", shouldReconnect ? "Reconectando..." : "Cerrado por logout.");
      if (shouldReconnect) {
        setTimeout(start, 3000);
      }
    }
  });
}

start().catch((err) => {
  console.error("❌ Error fatal:", err);
  process.exit(1);
});

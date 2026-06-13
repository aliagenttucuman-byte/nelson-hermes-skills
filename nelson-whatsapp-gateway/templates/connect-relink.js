const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require("@whiskeysockets/baileys");
const QRCode = require("qrcode");
const fs = require("fs");
const path = require("path");
const { exec } = require("child_process");

const AUTH_DIR = path.join(__dirname, "auth");
const QR_PATH = path.join(__dirname, "qr.png");

async function start() {
  console.log("\nÑÑ WhatsApp Gateway - Iniciando vinculacion...\n");

  const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);

  const sock = makeWASocket({ auth: state });

  sock.ev.on("creds.update", saveCreds);

  sock.ev.on("connection.update", async (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      await QRCode.toFile(QR_PATH, qr, { width: 600 });
      console.log("\n==================================================");
      console.log("  ÑÂ· CODIGO QR GUARDADO EN:");
      console.log(`  ${QR_PATH}`);
      console.log("==================================================\n");
      console.log("ÑÂ¹ En su celular: WhatsApp > Â·Â·Â· > Dispositivos vinculados > Vincular");
      console.log("ÑÂ¹ Escanee el QR.\n");

      exec(`xdg-open "${QR_PATH}"`, (err) => {
        if (err) console.log("No se pudo abrir la imagen automaticamente. Abrala manualmente.");
      });
    }

    if (connection === "open") {
      console.log("\nÂ¡ CONECTADO! WhatsApp Gateway listo.\n");
      if (fs.existsSync(QR_PATH)) fs.unlinkSync(QR_PATH);
      setTimeout(() => process.exit(0), 5000);
    }

    if (connection === "close") {
      const statusCode = lastDisconnect?.error?.output?.statusCode;
      const shouldReconnect = statusCode !== DisconnectReason.loggedOut;
      console.log("\nÂ¦Â° Conexion cerrada.", shouldReconnect ? "Reconectando..." : "Cerrado por logout.");
      if (shouldReconnect) setTimeout(start, 3000);
    }
  });
}

start().catch((err) => {
  console.error("Â§ Error fatal:", err);
  process.exit(1);
});

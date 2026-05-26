/**
 * Chat route — patrón correcto para OpenUI + Groq
 *
 * El frontend llama DIRECTO al SDK de OpenAI (apuntando a Groq),
 * no hace proxy a través del backend. El backend solo provee /api/system-prompt.
 *
 * POR QUÉ: OpenUI espera response.toReadableStream() del SDK de OpenAI.
 * Si el backend reenvía bytes SSE crudos, el parser explota con:
 *   SyntaxError: Unexpected token 'd', "data: {\"id\"... is not valid JSON
 */
import { NextRequest } from "next/server";
import OpenAI from "openai";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8765";

const client = new OpenAI({
  apiKey: process.env.GROQ_API_KEY || "",
  baseURL: "https://api.groq.com/openai/v1",
});

async function getSystemPrompt(): Promise<string> {
  try {
    const res = await fetch(`${BACKEND_URL}/api/system-prompt`);
    const data = await res.json();
    return data.systemPrompt || "";
  } catch {
    return "";
  }
}

export async function POST(req: NextRequest) {
  try {
    const { messages, systemPrompt: frontendPrompt } = await req.json();
    const backendPrompt = await getSystemPrompt();
    const systemPrompt = [frontendPrompt, backendPrompt].filter(Boolean).join("\n\n");

    const response = await client.chat.completions.create({
      model: "llama-3.3-70b-versatile",
      messages: [
        { role: "system", content: systemPrompt },
        ...messages,
      ],
      stream: true,
    });

    // toReadableStream() produce el formato que OpenUI espera — no usar bytes crudos
    return new Response(response.toReadableStream(), {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache, no-transform",
        Connection: "keep-alive",
      },
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}

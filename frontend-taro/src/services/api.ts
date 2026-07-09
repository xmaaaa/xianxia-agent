import type { Character } from "@/store/session";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

export type CreateCharacterPayload = {
  userId: string;
  name: string;
  background?: string;
};

export type ChatPayload = {
  userId: string;
  characterId: string;
  message: string;
};

export function getApiBaseUrl() {
  return process.env.TARO_APP_API_BASE_URL || DEFAULT_API_BASE_URL;
}

export async function listCharacters(userId: string): Promise<Character[]> {
  void userId;
  return [];
}

export async function createCharacter(payload: CreateCharacterPayload): Promise<Character> {
  return {
    id: `local-${Date.now()}`,
    name: payload.name,
    realm: "炼气一层",
    cultivation: 0,
    location: "青岚山脚",
    inventory: ["粗布行囊"],
    recentEvents: [payload.background || "初入修行路"]
  };
}

export async function sendChat(payload: ChatPayload) {
  void payload;
  return {
    reply: "此处已预留后端对话接入。Phase 3b 会连接 FastAPI 的非流式聊天接口。",
    intent: "roleplay",
    actionSummary: ""
  };
}

import Taro from "@tarojs/taro";

import type { Character } from "@/store/session";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

export type CreateCharacterPayload = {
  userId: string;
  name: string;
  sect: string;
  spiritRoot: string;
};

export type ChatPayload = {
  userId: string;
  characterId: number;
  message: string;
};

export type ChatResult = {
  reply: string;
  intent: string;
  retrievedContext: string;
  gameDelta: Record<string, unknown>;
};

type ApiCharacter = {
  id: number;
  user_id: string;
  name: string;
  sect: string;
  spirit_root: string;
  realm: string;
  exp: number;
  location: string;
  inventory: string[];
  event_log: string[];
};

type ApiChatResponse = {
  reply: string;
  retrieved_context: string;
  current_intent: string;
  game_delta: Record<string, unknown>;
};

export function getApiBaseUrl() {
  const envBaseUrl =
    typeof process !== "undefined" && process.env
      ? process.env.TARO_APP_API_BASE_URL
      : "";
  return envBaseUrl || DEFAULT_API_BASE_URL;
}

function normalizeBaseUrl() {
  return getApiBaseUrl().replace(/\/$/, "");
}

function toCharacter(row: ApiCharacter): Character {
  return {
    id: row.id,
    userId: row.user_id,
    name: row.name,
    sect: row.sect,
    spiritRoot: row.spirit_root,
    realm: row.realm,
    cultivation: row.exp,
    location: row.location,
    inventory: row.inventory || [],
    recentEvents: row.event_log || []
  };
}

function getErrorMessage(data: unknown, fallback: string) {
  if (data && typeof data === "object" && "detail" in data) {
    const detail = (data as { detail?: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map((item) => JSON.stringify(item)).join("\n");
  }
  return fallback;
}

async function request<T>(path: string, options: Omit<Taro.request.Option, "url"> = {}): Promise<T> {
  const response = await Taro.request<T>({
    ...options,
    url: `${normalizeBaseUrl()}${path}`,
    header: {
      "content-type": "application/json",
      ...(options.header || {})
    }
  });

  if (response.statusCode < 200 || response.statusCode >= 300) {
    throw new Error(getErrorMessage(response.data, `请求失败：${response.statusCode}`));
  }

  return response.data;
}

export async function listCharacters(userId: string): Promise<Character[]> {
  const rows = await request<ApiCharacter[]>(`/api/v1/characters/?user_id=${encodeURIComponent(userId)}`, {
    method: "GET"
  });
  return rows.map(toCharacter);
}

export async function createCharacter(payload: CreateCharacterPayload): Promise<Character> {
  const row = await request<ApiCharacter>("/api/v1/characters/", {
    method: "POST",
    data: {
      user_id: payload.userId,
      name: payload.name,
      sect: payload.sect,
      spirit_root: payload.spiritRoot,
      realm: "炼气初期",
      exp: 0,
      location: "青云镇",
      inventory: ["粗布行囊"],
      event_log: ["初入修行路"]
    }
  });
  return toCharacter(row);
}

export async function getCharacter(userId: string, characterId: number): Promise<Character> {
  const row = await request<ApiCharacter>(
    `/api/v1/characters/${characterId}?user_id=${encodeURIComponent(userId)}`,
    {
      method: "GET"
    }
  );
  return toCharacter(row);
}

export async function sendChat(payload: ChatPayload): Promise<ChatResult> {
  const result = await request<ApiChatResponse>("/api/v1/chat/", {
    method: "POST",
    data: {
      user_id: payload.userId,
      character_id: payload.characterId,
      message: payload.message,
      stream: false
    }
  });

  return {
    reply: result.reply,
    intent: result.current_intent,
    retrievedContext: result.retrieved_context,
    gameDelta: result.game_delta
  };
}

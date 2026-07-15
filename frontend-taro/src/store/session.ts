import Taro from "@tarojs/taro";

export type Character = {
  id: number;
  userId: string;
  name: string;
  sect: string;
  spiritRoot: string;
  realm: string;
  cultivation: number;
  location: string;
  inventory: string[];
  recentEvents: string[];
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

const CHARACTER_KEY = "xianxia:selected-character";
const CHAT_KEY = "xianxia:chat-messages";
const USER_ID_KEY = "xianxia:user-id";

export const DEFAULT_USER_ID = "demo-user";

export const demoCharacter: Character = {
  id: 0,
  userId: DEFAULT_USER_ID,
  name: "云游散修",
  sect: "散修",
  spiritRoot: "五行杂灵根",
  realm: "炼气一层",
  cultivation: 12,
  location: "青岚山脚",
  inventory: ["养气丹", "粗布行囊"],
  recentEvents: ["在青岚山脚醒来", "听闻山中有灵草出没"]
};

export function loadUserId(): string {
  return Taro.getStorageSync<string>(USER_ID_KEY) || DEFAULT_USER_ID;
}

export function saveUserId(userId: string) {
  Taro.setStorageSync(USER_ID_KEY, userId || DEFAULT_USER_ID);
}

export function loadCharacter(): Character | undefined {
  return Taro.getStorageSync<Character>(CHARACTER_KEY) || undefined;
}

export function saveCharacter(character: Character) {
  Taro.setStorageSync(CHARACTER_KEY, character);
}

export function clearCharacter() {
  Taro.removeStorageSync(CHARACTER_KEY);
}

export function loadMessages(): ChatMessage[] {
  return (
    Taro.getStorageSync<ChatMessage[]>(CHAT_KEY) || [
      {
        id: "welcome",
        role: "assistant",
        content: "道友醒了。青岚山晨雾未散，今日想先探路，还是盘膝调息？"
      }
    ]
  );
}

export function saveMessages(messages: ChatMessage[]) {
  Taro.setStorageSync(CHAT_KEY, messages);
}

export function resetMessages() {
  Taro.removeStorageSync(CHAT_KEY);
}

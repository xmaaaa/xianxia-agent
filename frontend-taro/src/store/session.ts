import Taro from "@tarojs/taro";

export type Character = {
  id: string;
  name: string;
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

export const demoCharacter: Character = {
  id: "demo-character",
  name: "云游散修",
  realm: "炼气一层",
  cultivation: 12,
  location: "青岚山脚",
  inventory: ["养气丹", "粗布行囊"],
  recentEvents: ["在青岚山脚醒来", "听闻山中有灵草出没"]
};

export function loadCharacter(): Character {
  return Taro.getStorageSync<Character>(CHARACTER_KEY) || demoCharacter;
}

export function saveCharacter(character: Character) {
  Taro.setStorageSync(CHARACTER_KEY, character);
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

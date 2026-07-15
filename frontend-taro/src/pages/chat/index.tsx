import Taro, { useDidShow } from "@tarojs/taro";
import { Button, Input, ScrollView, Text, View } from "@tarojs/components";
import { useState } from "react";

import { getCharacter, sendChat } from "@/services/api";
import {
  loadCharacter,
  loadMessages,
  loadUserId,
  saveCharacter,
  saveMessages,
  type Character,
  type ChatMessage
} from "@/store/session";

import "./index.css";

const actions = ["探索", "查看属性", "修炼", "调息"];

export default function ChatPage() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>(loadMessages());
  const [character, setCharacter] = useState<Character | undefined>(loadCharacter());
  const [sending, setSending] = useState(false);
  const [intent, setIntent] = useState("");
  const [actionSummary, setActionSummary] = useState("");

  useDidShow(() => {
    setMessages(loadMessages());
    setCharacter(loadCharacter());
  });

  async function submit(content: string) {
    const trimmed = content.trim();
    if (!trimmed) return;
    if (!character) {
      Taro.showToast({ title: "请先创建角色", icon: "none" });
      Taro.redirectTo({ url: "/pages/create/index" });
      return;
    }

    const nextMessages: ChatMessage[] = [
      ...messages,
      { id: `user-${Date.now()}`, role: "user", content: trimmed }
    ];
    setMessages(nextMessages);
    saveMessages(nextMessages);
    setMessage("");
    setSending(true);

    try {
      const userId = loadUserId();
      const result = await sendChat({
        userId,
        characterId: character.id,
        message: trimmed
      });

      const withReply: ChatMessage[] = [
        ...nextMessages,
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: result.reply
        }
      ];
      setMessages(withReply);
      saveMessages(withReply);
      setIntent(result.intent);
      setActionSummary(summarizeDelta(result.gameDelta));

      const refreshed = await getCharacter(userId, character.id);
      saveCharacter(refreshed);
      setCharacter(refreshed);
    } catch (error) {
      const rollbackMessages: ChatMessage[] = [
        ...nextMessages,
        {
          id: `assistant-error-${Date.now()}`,
          role: "assistant",
          content: error instanceof Error ? error.message : "对话失败，请稍后再试。"
        }
      ];
      setMessages(rollbackMessages);
      saveMessages(rollbackMessages);
    } finally {
      setSending(false);
    }
  }

  function summarizeDelta(delta: Record<string, unknown>) {
    const parts: string[] = [];
    if (typeof delta.exp_delta === "number" && delta.exp_delta > 0) parts.push(`修为 +${delta.exp_delta}`);
    if (typeof delta.realm === "string") parts.push(`境界 ${delta.realm}`);
    if (typeof delta.location === "string") parts.push(`位置 ${delta.location}`);
    if (Array.isArray(delta.items_add) && delta.items_add.length > 0) parts.push(`获得 ${delta.items_add.join("、")}`);
    if (Array.isArray(delta.items_remove) && delta.items_remove.length > 0) parts.push(`消耗 ${delta.items_remove.join("、")}`);
    return parts.join(" · ");
  }

  return (
    <View className="page chat-page">
      <View className="chat-header">
        <View>
          <Text className="panel-title">{character?.name || "未选择角色"}</Text>
          <Text className="muted">
            {character ? `${character.realm} · ${character.location}` : "先创建角色"}
          </Text>
        </View>
        <Button className="button ghost header-button" onClick={() => Taro.navigateTo({ url: "/pages/character/index" })}>
          面板
        </Button>
      </View>

      {(intent || actionSummary) && (
        <View className="status-strip">
          {intent && <Text>{intent}</Text>}
          {actionSummary && <Text>{actionSummary}</Text>}
        </View>
      )}

      <ScrollView className="message-list" scrollY>
        {messages.map((item) => (
          <View key={item.id} className={`message ${item.role}`}>
            <Text>{item.content}</Text>
          </View>
        ))}
      </ScrollView>

      <View className="action-row">
        {actions.map((action) => (
          <Button key={action} className="button ghost action-button" disabled={sending || !character} onClick={() => submit(action)}>
            {action}
          </Button>
        ))}
      </View>

      <View className="composer">
        <Input className="input composer-input" value={message} placeholder="和叙事之灵说些什么" onInput={(event) => setMessage(event.detail.value)} />
        <Button className="button send-button" loading={sending} disabled={sending || !character} onClick={() => submit(message)}>
          发送
        </Button>
      </View>
    </View>
  );
}

import Taro, { useDidShow } from "@tarojs/taro";
import { Button, Input, ScrollView, Text, View } from "@tarojs/components";
import { useState } from "react";

import { sendChat } from "@/services/api";
import { loadCharacter, loadMessages, saveMessages, type ChatMessage } from "@/store/session";

import "./index.css";

const actions = ["探索", "查看属性", "修炼", "调息"];

export default function ChatPage() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>(loadMessages());
  const character = loadCharacter();

  useDidShow(() => {
    setMessages(loadMessages());
  });

  async function submit(content: string) {
    const trimmed = content.trim();
    if (!trimmed) return;

    const nextMessages: ChatMessage[] = [
      ...messages,
      { id: `user-${Date.now()}`, role: "user", content: trimmed }
    ];
    setMessages(nextMessages);
    saveMessages(nextMessages);
    setMessage("");

    const result = await sendChat({
      userId: "demo-user",
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
  }

  return (
    <View className="page chat-page">
      <View className="chat-header">
        <View>
          <Text className="panel-title">{character.name}</Text>
          <Text className="muted">
            {character.realm} · {character.location}
          </Text>
        </View>
        <Button className="button ghost header-button" onClick={() => Taro.navigateTo({ url: "/pages/character/index" })}>
          面板
        </Button>
      </View>

      <ScrollView className="message-list" scrollY>
        {messages.map((item) => (
          <View key={item.id} className={`message ${item.role}`}>
            <Text>{item.content}</Text>
          </View>
        ))}
      </ScrollView>

      <View className="action-row">
        {actions.map((action) => (
          <Button key={action} className="button ghost action-button" onClick={() => submit(action)}>
            {action}
          </Button>
        ))}
      </View>

      <View className="composer">
        <Input className="input composer-input" value={message} placeholder="和叙事之灵说些什么" onInput={(event) => setMessage(event.detail.value)} />
        <Button className="button send-button" onClick={() => submit(message)}>
          发送
        </Button>
      </View>
    </View>
  );
}

import Taro, { useDidShow } from "@tarojs/taro";
import { Button, Text, View } from "@tarojs/components";
import { useState } from "react";

import { loadCharacter, type Character } from "@/store/session";

import "./index.css";

export default function IndexPage() {
  const [character, setCharacter] = useState<Character>(loadCharacter());

  useDidShow(() => {
    setCharacter(loadCharacter());
  });

  return (
    <View className="page">
      <View className="topbar">
        <View>
          <Text className="title">修仙 Agent</Text>
          <Text className="subtitle">选择角色，进入今日修行。</Text>
        </View>
      </View>

      <View className="stack">
        <View className="panel character-card">
          <Text className="panel-title">{character.name}</Text>
          <Text className="muted">
            {character.realm} · {character.location}
          </Text>
          <View className="progress">
            <View className="progress-fill" style={{ width: `${Math.min(character.cultivation, 100)}%` }} />
          </View>
          <Text className="muted">修为进度 {character.cultivation}/100</Text>
        </View>

        <Button className="button" onClick={() => Taro.navigateTo({ url: "/pages/chat/index" })}>
          进入对话
        </Button>
        <Button className="button secondary" onClick={() => Taro.navigateTo({ url: "/pages/create/index" })}>
          创建新角色
        </Button>
        <View className="quick-grid">
          <Button className="button ghost" onClick={() => Taro.navigateTo({ url: "/pages/character/index" })}>
            角色面板
          </Button>
          <Button className="button ghost" onClick={() => Taro.navigateTo({ url: "/pages/inventory/index" })}>
            背包
          </Button>
        </View>
      </View>
    </View>
  );
}

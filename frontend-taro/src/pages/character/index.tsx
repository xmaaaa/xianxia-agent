import Taro, { useDidShow } from "@tarojs/taro";
import { Text, View } from "@tarojs/components";
import { useState } from "react";

import { getCharacter } from "@/services/api";
import { loadCharacter, loadUserId, saveCharacter, type Character } from "@/store/session";

import "./index.css";

export default function CharacterPage() {
  const [character, setCharacter] = useState<Character | undefined>(loadCharacter());

  useDidShow(() => {
    refreshCharacter();
  });

  async function refreshCharacter() {
    const current = loadCharacter();
    if (!current) return;

    try {
      const refreshed = await getCharacter(loadUserId(), current.id);
      saveCharacter(refreshed);
      setCharacter(refreshed);
    } catch (error) {
      Taro.showToast({ title: error instanceof Error ? error.message : "角色状态加载失败", icon: "none" });
    }
  }

  if (!character) {
    return (
      <View className="page stack">
        <Text className="title">角色面板</Text>
        <Text className="subtitle">尚未选择角色。</Text>
      </View>
    );
  }

  return (
    <View className="page stack">
      <View>
        <Text className="title">{character.name}</Text>
        <Text className="subtitle">
          {character.sect} · {character.spiritRoot} · {character.location}
        </Text>
      </View>

      <View className="stat-grid">
        <View className="panel">
          <Text className="muted">境界</Text>
          <Text className="panel-title">{character.realm}</Text>
        </View>
        <View className="panel">
          <Text className="muted">修为</Text>
          <Text className="panel-title">{character.cultivation}/100</Text>
        </View>
      </View>

      <View className="panel stack">
        <Text className="panel-title">近事</Text>
        {character.recentEvents.map((event) => (
          <Text key={event} className="event-item">
            {event}
          </Text>
        ))}
      </View>
    </View>
  );
}

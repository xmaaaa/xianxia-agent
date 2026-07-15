import Taro, { useDidShow } from "@tarojs/taro";
import { Button, Text, View } from "@tarojs/components";
import { useState } from "react";

import { getCharacter, sendChat } from "@/services/api";
import { loadCharacter, loadUserId, saveCharacter, type Character } from "@/store/session";

import "./index.css";

export default function InventoryPage() {
  const [character, setCharacter] = useState<Character | undefined>(loadCharacter());
  const [usingItem, setUsingItem] = useState("");

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
      Taro.showToast({ title: error instanceof Error ? error.message : "背包加载失败", icon: "none" });
    }
  }

  async function useItem(item: string) {
    if (!character) return;

    setUsingItem(item);
    try {
      await sendChat({
        userId: loadUserId(),
        characterId: character.id,
        message: `使用${item}`
      });
      await refreshCharacter();
      Taro.showToast({ title: "已使用", icon: "success" });
    } catch (error) {
      Taro.showToast({ title: error instanceof Error ? error.message : "使用失败", icon: "none" });
    } finally {
      setUsingItem("");
    }
  }

  if (!character) {
    return (
      <View className="page stack">
        <Text className="title">背包</Text>
        <Text className="subtitle">尚未选择角色。</Text>
      </View>
    );
  }

  return (
    <View className="page stack">
      <View>
        <Text className="title">背包</Text>
        <Text className="subtitle">{character.name} 当前携带之物。</Text>
      </View>

      <View className="stack">
        {character.inventory.map((item) => (
          <View key={item} className="panel item-row">
            <Text className="panel-title">{item}</Text>
            <Button className="button ghost use-button" loading={usingItem === item} disabled={Boolean(usingItem)} onClick={() => useItem(item)}>
              使用
            </Button>
          </View>
        ))}
        {character.inventory.length === 0 && <Text className="muted">背包空空如也</Text>}
      </View>
    </View>
  );
}

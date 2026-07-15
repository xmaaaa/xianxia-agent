import Taro, { useDidShow } from "@tarojs/taro";
import { Button, Input, Text, View } from "@tarojs/components";
import { useState } from "react";

import { listCharacters } from "@/services/api";
import {
  clearCharacter,
  loadCharacter,
  loadUserId,
  resetMessages,
  saveCharacter,
  saveUserId,
  type Character
} from "@/store/session";

import "./index.css";

export default function IndexPage() {
  const [userId, setUserId] = useState(loadUserId());
  const [character, setCharacter] = useState<Character | undefined>(loadCharacter());
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState("");

  useDidShow(() => {
    const storedUserId = loadUserId();
    setUserId(storedUserId);
    setCharacter(loadCharacter());
    refreshCharacters(storedUserId);
  });

  async function refreshCharacters(nextUserId = userId) {
    const trimmed = nextUserId.trim();
    if (!trimmed) return;

    setLoading(true);
    setLoadError("");
    try {
      const rows = await listCharacters(trimmed);
      setCharacters(rows);
      const selected = loadCharacter();
      const nextSelected = rows.find((item) => item.id === selected?.id) || rows[0];
      if (nextSelected) {
        saveCharacter(nextSelected);
        setCharacter(nextSelected);
      } else {
        clearCharacter();
        setCharacter(undefined);
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "角色列表加载失败";
      setLoadError(message);
      setCharacters([]);
      clearCharacter();
      setCharacter(undefined);
      Taro.showToast({ title: message, icon: "none" });
    } finally {
      setLoading(false);
    }
  }

  function handleUserIdBlur() {
    const trimmed = userId.trim() || "demo-user";
    setUserId(trimmed);
    saveUserId(trimmed);
    refreshCharacters(trimmed);
  }

  function handleUserIdInput(value: string) {
    setUserId(value);
    saveUserId(value.trim() || "demo-user");
  }

  function selectCharacter(nextCharacter: Character) {
    saveCharacter(nextCharacter);
    resetMessages();
    setCharacter(nextCharacter);
  }

  return (
    <View className="page">
      <View className="topbar">
        <View>
          <Text className="title">修仙 Agent</Text>
          <Text className="subtitle">选择角色，进入今日修行。</Text>
        </View>
      </View>

      <View className="stack">
        <View className="panel stack">
          <Text className="panel-title">用户</Text>
          <Input className="input compact-input" value={userId} placeholder="user_id" onInput={(event) => handleUserIdInput(event.detail.value)} onBlur={handleUserIdBlur} />
          <Button className="button ghost" loading={loading} disabled={loading} onClick={() => refreshCharacters(userId)}>
            刷新角色
          </Button>
        </View>

        {character ? (
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
        ) : (
          <View className="panel character-card">
            <Text className="panel-title">未绑定角色</Text>
            <Text className="muted">请先选择已有角色，或创建一个新角色。</Text>
          </View>
        )}

        <View className="stack">
          <Text className="panel-title">可选择角色</Text>
          {characters.map((item) => (
            <Button
              key={item.id}
              className={`button ${item.id === character?.id ? "" : "secondary"}`}
              onClick={() => selectCharacter(item)}
            >
              {item.id === character?.id ? "已选择" : "选择"} · {item.name} · {item.realm}
            </Button>
          ))}
          {loading && <Text className="muted">正在加载角色...</Text>}
          {!loading && loadError && <Text className="muted">{loadError}</Text>}
          {!loading && !loadError && characters.length === 0 && <Text className="muted">当前用户暂无角色</Text>}
        </View>

        <Button className="button" disabled={!character} onClick={() => Taro.navigateTo({ url: "/pages/chat/index" })}>
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

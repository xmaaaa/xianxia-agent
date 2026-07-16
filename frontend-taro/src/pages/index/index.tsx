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
        <View className="panel user-panel">
          <View className="section-head">
            <View>
              <Text className="eyebrow">当前用户</Text>
              <Text className="muted">本地开发模式</Text>
            </View>
            <Button className="button ghost compact refresh-button" loading={loading} disabled={loading} onClick={() => refreshCharacters(userId)}>
              刷新
            </Button>
          </View>
          <Input className="input compact-input" value={userId} placeholder="user_id" onInput={(event) => handleUserIdInput(event.detail.value)} onBlur={handleUserIdBlur} />
        </View>

        {character ? (
          <View className="panel character-card active-character">
            <Text className="eyebrow">当前角色</Text>
            <View className="character-main">
              <View>
                <Text className="panel-title">{character.name}</Text>
                <Text className="muted">
                  {character.realm} · {character.location}
                </Text>
              </View>
              <Text className="badge">{character.sect}</Text>
            </View>
            <View className="progress">
              <View className="progress-fill" style={{ width: `${Math.min(character.cultivation, 100)}%` }} />
            </View>
            <View className="meta-row">
              <Text className="badge">修为 {character.cultivation}/100</Text>
              <Text className="badge">{character.spiritRoot}</Text>
            </View>
          </View>
        ) : (
          <View className="empty-state">
            <Text className="panel-title">未绑定角色</Text>
            <Text className="muted">创建角色后会自动绑定，也可以从下方列表选择已有角色。</Text>
          </View>
        )}

        <Button className="button" disabled={!character} onClick={() => Taro.navigateTo({ url: "/pages/chat/index" })}>
          进入对话
        </Button>

        <View className="panel stack">
          <View className="section-head">
            <View>
              <Text className="eyebrow">角色列表</Text>
              <Text className="muted">{characters.length ? `${characters.length} 个角色可用` : "按用户 ID 查询后选择"}</Text>
            </View>
            <Button className="button secondary compact create-button" onClick={() => Taro.navigateTo({ url: "/pages/create/index" })}>
              创建
            </Button>
          </View>

          {characters.map((item) => (
            <View key={item.id} className={`role-card ${item.id === character?.id ? "selected" : ""}`}>
              <View className="role-card-main">
                <View>
                  <Text className="panel-title">{item.name}</Text>
                  <Text className="muted">
                    {item.realm} · {item.location}
                  </Text>
                </View>
                <Button className={`button compact ${item.id === character?.id ? "" : "secondary"}`} onClick={() => selectCharacter(item)}>
                  {item.id === character?.id ? "已选择" : "选择"}
                </Button>
              </View>
              <View className="meta-row">
                <Text className="badge">{item.sect}</Text>
                <Text className="badge">修为 {item.cultivation}</Text>
              </View>
            </View>
          ))}

          {loading && <Text className="muted">正在加载角色...</Text>}
          {!loading && loadError && <Text className="muted">{loadError}</Text>}
          {!loading && !loadError && characters.length === 0 && (
            <View className="empty-state">
              <Text className="panel-title">当前用户暂无角色</Text>
              <Text className="muted">创建一个角色后就可以开始对话和行动。</Text>
            </View>
          )}
        </View>

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

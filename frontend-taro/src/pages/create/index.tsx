import Taro from "@tarojs/taro";
import { Button, Input, Text, Textarea, View } from "@tarojs/components";
import { useState } from "react";

import { createCharacter } from "@/services/api";
import { saveCharacter } from "@/store/session";

export default function CreatePage() {
  const [name, setName] = useState("");
  const [background, setBackground] = useState("");

  async function handleCreate() {
    const trimmedName = name.trim();
    if (!trimmedName) {
      Taro.showToast({ title: "请输入角色名", icon: "none" });
      return;
    }

    const character = await createCharacter({
      userId: "demo-user",
      name: trimmedName,
      background: background.trim()
    });
    saveCharacter(character);
    Taro.redirectTo({ url: "/pages/chat/index" });
  }

  return (
    <View className="page stack">
      <View>
        <Text className="title">创建角色</Text>
        <Text className="subtitle">先定下名号，后续再接入后端角色 API。</Text>
      </View>

      <View className="stack">
        <Input className="input" value={name} placeholder="角色名" onInput={(event) => setName(event.detail.value)} />
        <Textarea
          className="textarea"
          value={background}
          placeholder="出身、目标或一句执念"
          maxlength={120}
          onInput={(event) => setBackground(event.detail.value)}
        />
      </View>

      <Button className="button" onClick={handleCreate}>
        开始修行
      </Button>
    </View>
  );
}

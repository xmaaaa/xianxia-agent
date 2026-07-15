import Taro from "@tarojs/taro";
import { Button, Input, Text, Textarea, View } from "@tarojs/components";
import { useState } from "react";

import { createCharacter } from "@/services/api";
import { loadUserId, resetMessages, saveCharacter } from "@/store/session";

export default function CreatePage() {
  const [name, setName] = useState("");
  const [sect, setSect] = useState("散修");
  const [spiritRoot, setSpiritRoot] = useState("五行杂灵根");
  const [submitting, setSubmitting] = useState(false);

  async function handleCreate() {
    const trimmedName = name.trim();
    const trimmedSect = sect.trim();
    const trimmedSpiritRoot = spiritRoot.trim();
    if (!trimmedName) {
      Taro.showToast({ title: "请输入角色名", icon: "none" });
      return;
    }
    if (!trimmedSect || !trimmedSpiritRoot) {
      Taro.showToast({ title: "请补全宗门和灵根", icon: "none" });
      return;
    }

    setSubmitting(true);
    try {
      const character = await createCharacter({
        userId: loadUserId(),
        name: trimmedName,
        sect: trimmedSect,
        spiritRoot: trimmedSpiritRoot
      });
      saveCharacter(character);
      resetMessages();
      Taro.redirectTo({ url: "/pages/chat/index" });
    } catch (error) {
      Taro.showToast({ title: error instanceof Error ? error.message : "创建失败", icon: "none" });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <View className="page stack">
      <View>
        <Text className="title">创建角色</Text>
        <Text className="subtitle">定下名号、宗门与灵根。</Text>
      </View>

      <View className="stack">
        <Input className="input" value={name} placeholder="角色名" onInput={(event) => setName(event.detail.value)} />
        <Input className="input" value={sect} placeholder="宗门" onInput={(event) => setSect(event.detail.value)} />
        <Textarea className="textarea" value={spiritRoot} placeholder="灵根" maxlength={120} onInput={(event) => setSpiritRoot(event.detail.value)} />
      </View>

      <Button className="button" loading={submitting} disabled={submitting} onClick={handleCreate}>
        开始修行
      </Button>
    </View>
  );
}

import { Button, Text, View } from "@tarojs/components";

import { loadCharacter } from "@/store/session";

import "./index.css";

export default function InventoryPage() {
  const character = loadCharacter();

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
            <Button className="button ghost use-button">使用</Button>
          </View>
        ))}
      </View>
    </View>
  );
}

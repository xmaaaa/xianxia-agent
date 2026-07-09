import { Text, View } from "@tarojs/components";

import { loadCharacter } from "@/store/session";

import "./index.css";

export default function CharacterPage() {
  const character = loadCharacter();

  return (
    <View className="page stack">
      <View>
        <Text className="title">{character.name}</Text>
        <Text className="subtitle">{character.location}</Text>
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

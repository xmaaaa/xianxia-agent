from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1

from app.models.character import Character

REALM_THRESHOLDS: tuple[tuple[str, int], ...] = (
    ("炼气初期", 0),
    ("炼气中期", 20),
    ("炼气后期", 50),
    ("筑基初期", 100),
)

EXPLORE_SCENES: tuple[dict, ...] = (
    {
        "location": "青云镇外竹林",
        "exp_delta": 6,
        "item": "凝气草",
        "event": "在青云镇外竹林采得凝气草，丹田受灵气一洗。",
    },
    {
        "location": "寒潭石径",
        "exp_delta": 8,
        "item": "寒潭水珠",
        "event": "沿寒潭石径探查，收起一枚寒潭水珠。",
    },
    {
        "location": "废弃洞府",
        "exp_delta": 10,
        "item": "残破玉简",
        "event": "在废弃洞府发现残破玉简，隐约记下一缕古意。",
    },
)


@dataclass(frozen=True)
class CharacterSnapshot:
    user_id: str
    character_id: int
    realm: str = "炼气初期"
    exp: int = 0
    location: str = "青云镇"
    inventory: tuple[str, ...] = ()

    @classmethod
    def from_model(cls, row: Character) -> CharacterSnapshot:
        return cls(
            user_id=row.user_id,
            character_id=row.id,
            realm=row.realm,
            exp=row.exp,
            location=row.location,
            inventory=tuple(row.inventory or ()),
        )


def realm_for_exp(exp: int) -> str:
    realm = REALM_THRESHOLDS[0][0]
    for name, threshold in REALM_THRESHOLDS:
        if exp >= threshold:
            realm = name
    return realm


def _realm_delta(snapshot: CharacterSnapshot, exp_delta: int) -> dict:
    next_realm = realm_for_exp(snapshot.exp + exp_delta)
    if next_realm != snapshot.realm:
        return {"realm": next_realm, "breakthrough": True}
    return {}


def _stable_scene(snapshot: CharacterSnapshot, user_text: str) -> dict:
    seed = (
        f"{snapshot.user_id}:{snapshot.character_id}:{snapshot.exp}:{snapshot.location}:{user_text}"
    )
    idx = int(sha1(seed.encode("utf-8")).hexdigest(), 16) % len(EXPLORE_SCENES)
    return EXPLORE_SCENES[idx]


def plan_explore(snapshot: CharacterSnapshot, user_text: str) -> dict:
    scene = _stable_scene(snapshot, user_text)
    exp_delta = int(scene["exp_delta"])
    delta = {
        "type": "explore",
        "exp_delta": exp_delta,
        "location": scene["location"],
        "items_add": [scene["item"]],
        "event": scene["event"],
    }
    delta.update(_realm_delta(snapshot, exp_delta))
    return delta


def plan_cultivate(snapshot: CharacterSnapshot) -> dict:
    exp_delta = 12
    delta = {
        "type": "cultivate",
        "exp_delta": exp_delta,
        "event": f"在{snapshot.location}静坐吐纳，炼化一缕清气，修为增加{exp_delta}点。",
    }
    delta.update(_realm_delta(snapshot, exp_delta))
    if delta.get("breakthrough"):
        delta["event"] += f" 气机圆融，境界突破至{delta['realm']}。"
    return delta


def plan_rest(snapshot: CharacterSnapshot) -> dict:
    return {
        "type": "rest",
        "event": f"在{snapshot.location}调息片刻，心神渐定，灵台清明。",
    }


def plan_use_item(snapshot: CharacterSnapshot, user_text: str) -> dict:
    item = next((x for x in snapshot.inventory if x and x in user_text), "")
    if not item and snapshot.inventory:
        item = snapshot.inventory[0]
    if not item:
        return {
            "type": "use_item",
            "event": "翻检背包，却暂未找到可用之物。",
        }

    exp_delta = 5 if item in {"凝气草", "寒潭水珠"} else 3
    delta = {
        "type": "use_item",
        "exp_delta": exp_delta,
        "items_remove": [item],
        "event": f"使用{item}后，灵气入体，修为增加{exp_delta}点。",
    }
    delta.update(_realm_delta(snapshot, exp_delta))
    if delta.get("breakthrough"):
        delta["event"] += f" 借此机缘，境界突破至{delta['realm']}。"
    return delta


def plan_action(action: str, snapshot: CharacterSnapshot, user_text: str = "") -> dict:
    if action == "explore":
        return plan_explore(snapshot, user_text)
    if action == "cultivate":
        return plan_cultivate(snapshot)
    if action == "rest":
        return plan_rest(snapshot)
    if action == "use_item":
        return plan_use_item(snapshot, user_text)
    return {}


def format_delta_context(delta: dict) -> str:
    if not delta:
        return ""

    lines = ["本次行动将产生以下可落账结果：", f"- 行动：{delta.get('type', 'unknown')}"]
    if delta.get("location"):
        lines.append(f"- 地点：{delta['location']}")
    if delta.get("exp_delta"):
        lines.append(f"- 修为增加：{delta['exp_delta']}")
    if delta.get("realm"):
        lines.append(f"- 境界变化：{delta['realm']}")
    if delta.get("items_add"):
        lines.append(f"- 获得物品：{'、'.join(delta['items_add'])}")
    if delta.get("items_remove"):
        lines.append(f"- 消耗物品：{'、'.join(delta['items_remove'])}")
    if delta.get("event"):
        lines.append(f"- 事件：{delta['event']}")
    return "\n".join(lines)

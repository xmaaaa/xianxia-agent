from app.game.engine import (
    CharacterSnapshot,
    format_delta_context,
    plan_action,
    realm_for_exp,
)


def test_realm_for_exp_uses_highest_reached_threshold():
    assert realm_for_exp(0) == "炼气初期"
    assert realm_for_exp(20) == "炼气中期"
    assert realm_for_exp(55) == "炼气后期"
    assert realm_for_exp(120) == "筑基初期"


def test_cultivate_can_break_through():
    snapshot = CharacterSnapshot(user_id="u1", character_id=1, exp=15, realm="炼气初期")
    delta = plan_action("cultivate", snapshot)

    assert delta["type"] == "cultivate"
    assert delta["exp_delta"] == 12
    assert delta["realm"] == "炼气中期"
    assert delta["breakthrough"] is True


def test_use_item_consumes_matching_inventory_item():
    snapshot = CharacterSnapshot(
        user_id="u1",
        character_id=1,
        inventory=("凝气草", "残破玉简"),
    )
    delta = plan_action("use_item", snapshot, "服用凝气草")

    assert delta["type"] == "use_item"
    assert delta["items_remove"] == ["凝气草"]
    assert delta["exp_delta"] == 5


def test_format_delta_context_mentions_material_changes():
    text = format_delta_context(
        {
            "type": "use_item",
            "exp_delta": 5,
            "realm": "炼气中期",
            "items_remove": ["凝气草"],
            "event": "使用凝气草后，灵气入体。",
        }
    )

    assert "行动：use_item" in text
    assert "修为增加：5" in text
    assert "境界变化：炼气中期" in text
    assert "消耗物品：凝气草" in text

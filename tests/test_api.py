def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_create_and_list_character(client):
    payload = {
        "user_id": "test-user-1",
        "name": "云游子",
        "sect": "太清宗",
        "spirit_root": "水木双灵根",
    }
    r = client.post("/api/v1/characters/", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "云游子"
    assert data["realm"] == "炼气初期"
    assert data["exp"] == 0
    assert data["location"] == "青云镇"
    assert data["inventory"] == []
    assert data["event_log"] == []
    cid = data["id"]

    r = client.get("/api/v1/characters/", params={"user_id": "test-user-1"})
    assert r.status_code == 200
    ids = [c["id"] for c in r.json()]
    assert cid in ids


def test_get_character_wrong_user(client):
    payload = {
        "user_id": "owner",
        "name": "剑仙",
        "sect": "蜀山",
        "spirit_root": "金灵根",
    }
    r = client.post("/api/v1/characters/", json=payload)
    cid = r.json()["id"]

    r = client.get(f"/api/v1/characters/{cid}", params={"user_id": "stranger"})
    assert r.status_code == 404


def test_update_character(client):
    payload = {
        "user_id": "u2",
        "name": "初名",
        "sect": "散修",
        "spirit_root": "火灵根",
    }
    r = client.post("/api/v1/characters/", json=payload)
    cid = r.json()["id"]

    r = client.patch(
        f"/api/v1/characters/{cid}",
        params={"user_id": "u2"},
        json={"name": "新名", "realm": "筑基初期"},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "新名"
    assert r.json()["realm"] == "筑基初期"


def test_delete_character(client):
    payload = {
        "user_id": "u3",
        "name": "将删",
        "sect": "无",
        "spirit_root": "无灵根",
    }
    r = client.post("/api/v1/characters/", json=payload)
    cid = r.json()["id"]

    r = client.delete(f"/api/v1/characters/{cid}", params={"user_id": "u3"})
    assert r.status_code == 204

    r = client.get(f"/api/v1/characters/{cid}", params={"user_id": "u3"})
    assert r.status_code == 404


def test_chat_requires_openai_key(client, mock_redis, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.openai_api_key", "")

    payload = {
        "user_id": "u1",
        "name": "测试",
        "sect": "测试宗",
        "spirit_root": "测试灵根",
    }
    r = client.post("/api/v1/characters/", json=payload)
    cid = r.json()["id"]

    r = client.post(
        "/api/v1/chat/",
        json={
            "user_id": "u1",
            "character_id": cid,
            "message": "你好",
            "stream": False,
        },
    )
    assert r.status_code == 503
    assert "语言模型" in r.json()["detail"]


def test_chat_explore_updates_character_state(client, mock_redis, mock_openai):
    payload = {
        "user_id": "u-explore",
        "name": "探幽子",
        "sect": "太清宗",
        "spirit_root": "木灵根",
    }
    r = client.post("/api/v1/characters/", json=payload)
    cid = r.json()["id"]

    r = client.post(
        "/api/v1/chat/",
        json={
            "user_id": "u-explore",
            "character_id": cid,
            "message": "探索一下周围有什么",
            "stream": False,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["current_intent"] == "explore"
    assert data["game_delta"]["type"] == "explore"

    r = client.get(f"/api/v1/characters/{cid}", params={"user_id": "u-explore"})
    assert r.status_code == 200
    char = r.json()
    assert char["exp"] > 0
    assert char["location"] != "青云镇"
    assert char["inventory"]
    assert char["event_log"]


def test_chat_cultivate_can_break_through(client, mock_redis, mock_openai):
    payload = {
        "user_id": "u-cultivate",
        "name": "炼气子",
        "sect": "太清宗",
        "spirit_root": "木灵根",
        "exp": 15,
    }
    r = client.post("/api/v1/characters/", json=payload)
    cid = r.json()["id"]

    r = client.post(
        "/api/v1/chat/",
        json={
            "user_id": "u-cultivate",
            "character_id": cid,
            "message": "我要开始修炼",
            "stream": False,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["current_intent"] == "cultivate"
    assert data["game_delta"]["realm"] == "炼气中期"

    r = client.get(f"/api/v1/characters/{cid}", params={"user_id": "u-cultivate"})
    assert r.status_code == 200
    char = r.json()
    assert char["exp"] == 27
    assert char["realm"] == "炼气中期"
    assert char["event_log"]

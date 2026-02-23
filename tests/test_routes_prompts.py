"""Tests for /api/prompts — Full CRUD, partial update."""

import pytest


async def test_create_prompt(client):
    resp = await client.post("/api/prompts", json={"name": "Greeting", "prompt": "Say hello"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Greeting"
    assert data["prompt"] == "Say hello"
    assert data["temperature"] == 0.7
    assert data["max_tokens"] == 2048
    assert data["id"]


async def test_create_prompt_all_fields(client):
    resp = await client.post("/api/prompts", json={
        "name": "Code",
        "prompt": "Write Python",
        "system_prompt": "Be concise",
        "temperature": 0.3,
        "max_tokens": 512,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["system_prompt"] == "Be concise"
    assert data["temperature"] == 0.3
    assert data["max_tokens"] == 512


async def test_create_prompt_validation_error(client):
    resp = await client.post("/api/prompts", json={"name": "X"})
    assert resp.status_code == 422


async def test_list_prompts_empty(client):
    resp = await client.get("/api/prompts")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_prompts_ordered_by_updated_at(client):
    await client.post("/api/prompts", json={"name": "First", "prompt": "A"})
    await client.post("/api/prompts", json={"name": "Second", "prompt": "B"})
    resp = await client.get("/api/prompts")
    data = resp.json()
    assert len(data) == 2
    # Most recently created (updated) should come first
    assert data[0]["name"] == "Second"
    assert data[1]["name"] == "First"


async def test_get_prompt_by_id(client):
    create = await client.post("/api/prompts", json={"name": "X", "prompt": "Y"})
    pid = create.json()["id"]
    resp = await client.get(f"/api/prompts/{pid}")
    assert resp.status_code == 200
    assert resp.json()["id"] == pid


async def test_get_prompt_404(client):
    resp = await client.get("/api/prompts/nonexistent-id")
    assert resp.status_code == 404


async def test_update_prompt_partial(client):
    create = await client.post("/api/prompts", json={"name": "Old", "prompt": "Hello"})
    pid = create.json()["id"]
    resp = await client.put(f"/api/prompts/{pid}", json={"name": "New"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "New"
    assert data["prompt"] == "Hello"  # unchanged


async def test_update_prompt_full(client):
    create = await client.post("/api/prompts", json={"name": "Old", "prompt": "Hello"})
    pid = create.json()["id"]
    resp = await client.put(f"/api/prompts/{pid}", json={
        "name": "Updated",
        "prompt": "World",
        "temperature": 1.0,
        "max_tokens": 1024,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated"
    assert data["prompt"] == "World"
    assert data["temperature"] == 1.0
    assert data["max_tokens"] == 1024


async def test_update_prompt_404(client):
    resp = await client.put("/api/prompts/nonexistent", json={"name": "New"})
    assert resp.status_code == 404


async def test_delete_prompt(client):
    create = await client.post("/api/prompts", json={"name": "Gone", "prompt": "Bye"})
    pid = create.json()["id"]
    resp = await client.delete(f"/api/prompts/{pid}")
    assert resp.status_code == 204

    # Confirm deleted
    resp2 = await client.get(f"/api/prompts/{pid}")
    assert resp2.status_code == 404


async def test_delete_prompt_404(client):
    resp = await client.delete("/api/prompts/nonexistent")
    assert resp.status_code == 404

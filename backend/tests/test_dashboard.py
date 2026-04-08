import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Auto-replies CRUD
class TestAutoReplies:
    """Auto-replies endpoint tests"""

    def test_get_auto_replies(self):
        r = requests.get(f"{BASE_URL}/api/auto-replies")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        print(f"Auto-replies count: {len(data)}")

    def test_create_auto_reply(self):
        payload = {"trigger": "TEST_test123", "response": "réponse test", "type": "exact"}
        r = requests.post(f"{BASE_URL}/api/auto-replies", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert data["trigger"] == "TEST_test123"
        assert data["response"] == "réponse test"
        assert "id" in data
        # cleanup
        requests.delete(f"{BASE_URL}/api/auto-replies/{data['id']}")

    def test_toggle_auto_reply(self):
        # Create one
        payload = {"trigger": "TEST_toggle", "response": "toggle test", "type": "exact", "active": True}
        r = requests.post(f"{BASE_URL}/api/auto-replies", json=payload)
        assert r.status_code == 200
        item = r.json()
        item_id = item["id"]
        # Toggle off
        r2 = requests.put(f"{BASE_URL}/api/auto-replies/{item_id}", json={"active": False})
        assert r2.status_code == 200
        assert r2.json()["active"] == False
        # cleanup
        requests.delete(f"{BASE_URL}/api/auto-replies/{item_id}")

    def test_delete_auto_reply(self):
        payload = {"trigger": "TEST_delete", "response": "delete test", "type": "exact"}
        r = requests.post(f"{BASE_URL}/api/auto-replies", json=payload)
        item_id = r.json()["id"]
        r2 = requests.delete(f"{BASE_URL}/api/auto-replies/{item_id}")
        assert r2.status_code == 200
        # Verify not found
        r3 = requests.delete(f"{BASE_URL}/api/auto-replies/{item_id}")
        assert r3.status_code == 404


class TestBannedWords:
    """Banned words endpoint tests"""

    def test_get_banned_words(self):
        r = requests.get(f"{BASE_URL}/api/banned-words")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        print(f"Banned words count: {len(data)}")

    def test_create_banned_word(self):
        payload = {"word": "testmot_unique_xyz", "category": "insultes"}
        r = requests.post(f"{BASE_URL}/api/banned-words", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert data["word"] == "testmot_unique_xyz"
        requests.delete(f"{BASE_URL}/api/banned-words/{data['id']}")

    def test_duplicate_banned_word(self):
        payload = {"word": "testmot_dup_xyz", "category": "insultes"}
        r1 = requests.post(f"{BASE_URL}/api/banned-words", json=payload)
        assert r1.status_code == 200
        r2 = requests.post(f"{BASE_URL}/api/banned-words", json=payload)
        assert r2.status_code == 409
        requests.delete(f"{BASE_URL}/api/banned-words/{r1.json()['id']}")


class TestCommands:
    """Commands endpoint tests"""

    def test_get_commands(self):
        r = requests.get(f"{BASE_URL}/api/commands")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        print(f"Commands count: {len(data)}")

    def test_create_command(self):
        payload = {"command": "!testcmd", "description": "Test commande", "category": "Fun"}
        r = requests.post(f"{BASE_URL}/api/commands", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert data["command"] == "!testcmd"
        requests.delete(f"{BASE_URL}/api/commands/{data['id']}")

    def test_delete_command(self):
        payload = {"command": "!testdelete", "description": "delete test", "category": "Jeux"}
        r = requests.post(f"{BASE_URL}/api/commands", json=payload)
        item_id = r.json()["id"]
        r2 = requests.delete(f"{BASE_URL}/api/commands/{item_id}")
        assert r2.status_code == 200


class TestSettings:
    """Settings endpoint tests"""

    def test_get_settings(self):
        r = requests.get(f"{BASE_URL}/api/settings")
        assert r.status_code == 200
        data = r.json()
        assert "bot_prefix" in data

    def test_update_settings(self):
        r = requests.get(f"{BASE_URL}/api/settings")
        original = r.json()
        updated = {**original, "bot_prefix": "!bot"}
        r2 = requests.put(f"{BASE_URL}/api/settings", json=updated)
        assert r2.status_code == 200
        assert r2.json()["bot_prefix"] == "!bot"
        # restore
        requests.put(f"{BASE_URL}/api/settings", json=original)


class TestStats:
    """Stats endpoint test"""

    def test_get_stats(self):
        r = requests.get(f"{BASE_URL}/api/stats")
        assert r.status_code == 200
        data = r.json()
        assert "auto_replies" in data
        assert "banned_words" in data
        assert "commands" in data
        print(f"Stats: {data}")


class TestActivity:
    """Activity log tests"""

    def test_get_activity(self):
        r = requests.get(f"{BASE_URL}/api/activity")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        print(f"Activity logs count: {len(data)}")

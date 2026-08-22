from fastapi.testclient import TestClient

from backend.admin.blogger_import import parse_blogger_export
from backend.engines.api import APIValidationError
from backend.main import create_app
from backend.tests.e2e_app import PASSWORD, seed


def _login(client: TestClient, email: str = "operator@example.test") -> dict[str, str]:
    response = client.post("/admin/api/session", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200
    return {"authorization": f"Bearer {response.json()['data']['access_token']}"}


def _export(body: str = "&lt;p&gt;Imported body&lt;/p&gt;") -> str:
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:app="http://purl.org/atom/app#">
  <entry>
    <category scheme="http://schemas.google.com/g/2005#kind" term="http://schemas.google.com/blogger/2008/kind#post" />
    <category scheme="http://www.blogger.com/atom/ns#" term="Migration" />
    <title type="text">Imported Blogger post</title>
    <content type="html">{body}</content>
    <link rel="alternate" href="https://old.example.test/2024/01/imported-blogger-post.html" />
  </entry>
  <entry><category term="http://schemas.google.com/blogger/2008/kind#comment" /><title>Comment</title></entry>
</feed>'''


def test_blogger_import_is_permission_checked_sanitized_and_draft_by_default() -> None:
    with TestClient(create_app(on_started=seed)) as client:
        payload = {"format": "blogger-atom", "xml": _export("&lt;p&gt;Safe&lt;/p&gt;&lt;script&gt;alert(1)&lt;/script&gt;"), "preserve_published": False}
        assert client.post("/admin/api/content/import", headers=_login(client, "viewer@example.test"), json=payload).status_code == 403
        response = client.post("/admin/api/content/import", headers=_login(client), json=payload)
        assert response.status_code == 200
        result = response.json()["data"]
        assert {key: result[key] for key in ("imported", "published", "drafts", "ignored")} == {"imported": 1, "published": 0, "drafts": 1, "ignored": 1}
        imported = result["items"][0]
        assert imported["state"] == "draft"
        assert imported["data"]["labels"] == ["Migration"]
        assert "script" not in imported["data"]["body"]
        assert client.get(f"/site/content/{imported['id']}").status_code == 404


def test_blogger_import_can_preserve_published_state_and_never_overwrites_slug() -> None:
    with TestClient(create_app(on_started=seed)) as client:
        headers = _login(client)
        payload = {"format": "blogger-atom", "xml": _export(), "preserve_published": True}
        first = client.post("/admin/api/content/import", headers=headers, json=payload)
        second = client.post("/admin/api/content/import", headers=headers, json=payload)
        assert first.status_code == second.status_code == 200
        assert first.json()["data"]["published"] == second.json()["data"]["published"] == 1
        items = [first.json()["data"]["items"][0], second.json()["data"]["items"][0]]
        assert len({item["data"]["slug"] for item in items}) == len(items)
        assert all(item["state"] == "published" for item in items)


def test_blogger_parser_rejects_active_xml_and_content_supports_large_articles() -> None:
    try:
        parse_blogger_export('<!DOCTYPE feed [<!ENTITY x "unsafe">]><feed>&x;</feed>')
        raise AssertionError("unsafe XML was accepted")
    except APIValidationError:
        pass
    with TestClient(create_app(on_started=seed)) as client:
        code = "x = 1\n" * 30_000
        response = client.post("/admin/api/content", headers=_login(client), json={
            "type_id": "post", "title": "Large code article",
            "data": {"slug": "large-code-article", "body": f"<pre><code>{code}</code></pre>"},
        })
        assert response.status_code == 200
        assert len(response.json()["data"]["data"]["body"]) > 100_000

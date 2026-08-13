"""
apps/topics/tests.py

JA: 検索セッション機能(search_session/API_CONTRACT_2.md)のエンドポイントを検証する。
    ・ルートTopic一覧の絞り込み(?parent=null)とhas_children
    ・ドリルダウン(children)が子Topic/常設KnowledgeNodeのみ返すこと
    ・再帰検索(search)がAI生成の類題を除外し、配下全体を対象にすること
    ・所有者以外からは404になること
VI: Kiểm tra các endpoint của tính năng phiên tìm kiếm (search_session/API_CONTRACT_2.md).
    - Lọc danh sách Topic gốc (?parent=null) và has_children
    - Duyệt sâu dần (children) chỉ trả về Topic con / KnowledgeNode cố định
    - Tìm kiếm đệ quy (search) loại trừ node類題 do AI sinh, tìm trong toàn bộ phạm vi con cháu
    - Không phải chủ sở hữu thì nhận 404
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import KnowledgeNode, Topic

User = get_user_model()


class SearchSessionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pass12345")
        self.other = User.objects.create_user(username="stranger", password="pass12345")
        self.client.force_login(self.user)

        self.math = Topic.objects.create(user=self.user, name="数学", position=0)
        self.algebra = Topic.objects.create(
            user=self.user, name="代数", parent=self.math, position=0
        )
        self.geometry = Topic.objects.create(
            user=self.user, name="幾何", parent=self.math, position=1
        )
        self.n1 = KnowledgeNode.objects.create(
            topic=self.algebra, title="一次方程式の基礎", content="x + 3 = 7 を解け"
        )
        self.n2 = KnowledgeNode.objects.create(
            topic=self.algebra, title="二次方程式", content="判別式の使い方"
        )
        # JA: AI生成の使い捨て類題。検索セッションには一切出てこないはず。
        # VI: Node類題 dùng một lần do AI sinh. Không được xuất hiện ở phiên tìm kiếm.
        KnowledgeNode.objects.create(
            topic=self.algebra, title="類題", content="dummy", origin_node=self.n1
        )

    def test_root_topics_only_with_parent_null(self):
        resp = self.client.get("/api/topics/?parent=null")
        self.assertEqual(resp.status_code, 200)
        ids = [t["id"] for t in resp.json()]
        self.assertEqual(ids, [str(self.math.id)])
        self.assertTrue(resp.json()[0]["has_children"])

    def test_topic_without_children_reports_false(self):
        # JA: geometry(幾何)は子もノードも持たないので、children経由で確認する。
        # VI: geometry (幾何) không có Topic con lẫn node, kiểm qua children.
        children_resp = self.client.get(f"/api/topics/{self.math.id}/children/")
        geometry_entry = next(
            t for t in children_resp.json()["topics"] if t["id"] == str(self.geometry.id)
        )
        self.assertFalse(geometry_entry["has_children"])

    def test_children_returns_child_topics_and_permanent_nodes_only(self):
        resp = self.client.get(f"/api/topics/{self.algebra.id}/children/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["topics"], [])
        node_titles = {n["title"] for n in data["nodes"]}
        self.assertEqual(node_titles, {"一次方程式の基礎", "二次方程式"})

    def test_search_finds_match_recursively_and_excludes_derived_nodes(self):
        resp = self.client.get(f"/api/topics/{self.math.id}/search/?q=一次")
        self.assertEqual(resp.status_code, 200)
        titles = [n["title"] for n in resp.json()]
        self.assertEqual(titles, ["一次方程式の基礎"])

    def test_search_matches_content_too(self):
        resp = self.client.get(f"/api/topics/{self.math.id}/search/?q=判別式")
        self.assertEqual(resp.status_code, 200)
        titles = [n["title"] for n in resp.json()]
        self.assertEqual(titles, ["二次方程式"])

    def test_search_without_query_returns_400(self):
        resp = self.client.get(f"/api/topics/{self.algebra.id}/search/")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json(), {"detail": "q is required"})

    def test_knowledge_node_detail_includes_topic_name(self):
        resp = self.client.get(f"/api/knowledge-nodes/{self.n1.id}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.json(),
            {
                "id": str(self.n1.id),
                "title": "一次方程式の基礎",
                "content": "x + 3 = 7 を解け",
                "topic": str(self.algebra.id),
                "topic_name": "代数",
            },
        )

    def test_other_user_cannot_access_children(self):
        self.client.force_login(self.other)
        resp = self.client.get(f"/api/topics/{self.math.id}/children/")
        self.assertEqual(resp.status_code, 404)

    def test_other_user_cannot_search(self):
        self.client.force_login(self.other)
        resp = self.client.get(f"/api/topics/{self.math.id}/search/?q=一次")
        self.assertEqual(resp.status_code, 404)

    def test_other_user_cannot_view_knowledge_node_detail(self):
        self.client.force_login(self.other)
        resp = self.client.get(f"/api/knowledge-nodes/{self.n1.id}/")
        self.assertEqual(resp.status_code, 404)

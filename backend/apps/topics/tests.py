"""
apps/topics/tests.py

JA: 検索セッション機能(search_session/API_CONTRACT_2.md)のエンドポイントを検証する。
    ・ルートTopic一覧の絞り込み(?parent=null)とhas_children
    ・ドリルダウン(children)が子TopicとKnowledgeNodeを返すこと
    ・再帰検索(search)が配下全体を対象にすること
    ・所有者以外からは404になること
    ・他アプリ向けの窓口(get_owned_topic / get_owned_knowledge_node)の所有権チェック
    【修正 2026-08-15】origin_node フィールド削除に追従できておらず、setUp が
    TypeError で落ちて全テストがエラーになっていたため、AI生成の類題ノードを
    前提とした fixture と表明を削除した。
VI: Kiểm tra các endpoint của tính năng phiên tìm kiếm (search_session/API_CONTRACT_2.md).
    - Lọc danh sách Topic gốc (?parent=null) và has_children
    - Duyệt sâu dần (children) trả về Topic con và KnowledgeNode
    - Tìm kiếm đệ quy (search) quét toàn bộ phạm vi con cháu
    - Không phải chủ sở hữu thì nhận 404
    - Kiểm tra quyền sở hữu ở cửa ngõ cho app khác (get_owned_topic / get_owned_knowledge_node)
    【Sửa 2026-08-15】Do chưa cập nhật theo việc xóa field origin_node, setUp bị
    TypeError khiến toàn bộ test lỗi; đã xóa fixture và assertion dựa trên node
    類題 do AI sinh.
"""

import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.common.exceptions import NotFound

from . import services
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

    def test_children_returns_child_topics_and_nodes(self):
        resp = self.client.get(f"/api/topics/{self.algebra.id}/children/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["topics"], [])
        node_titles = {n["title"] for n in data["nodes"]}
        self.assertEqual(node_titles, {"一次方程式の基礎", "二次方程式"})

    def test_search_finds_match_recursively(self):
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

    def test_children_ignores_stray_parent_null_query_param(self):
        # JA: get_queryset()のlist向け絞り込み(?parent=null)がchildren/searchにまで
        #     波及すると、parentを持つTopic(algebra)へのアクセスが誤って404になる。
        #     この回帰を防ぐ。
        # VI: Nếu bộ lọc ?parent=null (dành cho list) lan sang children/search, việc
        #     truy cập Topic có parent (algebra) sẽ bị 404 nhầm. Test này chặn hồi quy đó.
        resp = self.client.get(f"/api/topics/{self.algebra.id}/children/?parent=null")
        self.assertEqual(resp.status_code, 200)

    def test_search_ignores_stray_parent_null_query_param(self):
        resp = self.client.get(f"/api/topics/{self.algebra.id}/search/?q=一次&parent=null")
        self.assertEqual(resp.status_code, 200)
        titles = [n["title"] for n in resp.json()]
        self.assertEqual(titles, ["一次方程式の基礎"])

    def test_ai_search_returns_suggestion_list(self):
        resp = self.client.post(
            "/api/topics/ai-search/",
            {"description": "三角形や角度を扱う分野"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        suggestions = resp.json()["suggestions"]
        self.assertIsInstance(suggestions, list)
        self.assertGreaterEqual(len(suggestions), 1)
        self.assertLessEqual(len(suggestions), 5)

    def test_ai_search_without_description_returns_400(self):
        resp = self.client.post("/api/topics/ai-search/", {}, content_type="application/json")
        self.assertEqual(resp.status_code, 400)

    def test_search_records_history_newest_first(self):
        self.client.get(f"/api/topics/{self.algebra.id}/search/?q=一次")
        self.client.get(f"/api/topics/{self.math.id}/search/?q=判別式")

        resp = self.client.get("/api/search-history/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 2)
        # JA: 新しい順(直近の検索が先頭)。VI: Mới nhất trước (tìm kiếm gần nhất ở đầu).
        self.assertEqual([h["query"] for h in data], ["判別式", "一次"])
        self.assertEqual(data[0]["topic"], str(self.math.id))
        self.assertEqual(data[0]["topic_name"], "数学")

    def test_failed_search_does_not_record_history(self):
        self.client.get(f"/api/topics/{self.algebra.id}/search/")  # q無し→400
        resp = self.client.get("/api/search-history/")
        self.assertEqual(resp.json(), [])

    def test_other_user_cannot_see_search_history(self):
        self.client.get(f"/api/topics/{self.algebra.id}/search/?q=一次")
        self.client.force_login(self.other)
        resp = self.client.get("/api/search-history/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])


class OwnershipGatewayTests(TestCase):
    """
    JA: 他アプリ(apps/chat 等)がTopic/KnowledgeNodeを取りに来るときの窓口が、
        所有者チェックを必ず行うことを保証する。ここが緩いと、他人のノードに
        自分のチャットセッションを紐付けられてしまう。
    VI: Bảo đảm cửa ngõ cho app khác (apps/chat...) lấy Topic/KnowledgeNode luôn
        kiểm tra chủ sở hữu. Nếu chỗ này lỏng, user có thể gắn phiên chat của
        mình vào node của người khác.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="owner2", password="pass12345")
        self.other = User.objects.create_user(username="stranger2", password="pass12345")
        self.topic = Topic.objects.create(user=self.user, name="数学", position=0)
        self.node = KnowledgeNode.objects.create(
            topic=self.topic, title="一次方程式", content="x + 3 = 7"
        )

    def test_get_owned_knowledge_node_returns_own_node(self):
        node = services.get_owned_knowledge_node(user=self.user, node_id=self.node.id)
        self.assertEqual(node.id, self.node.id)

    def test_get_owned_knowledge_node_rejects_other_users_node(self):
        with self.assertRaises(NotFound):
            services.get_owned_knowledge_node(user=self.other, node_id=self.node.id)

    def test_get_owned_knowledge_node_rejects_unknown_id(self):
        with self.assertRaises(NotFound):
            services.get_owned_knowledge_node(user=self.user, node_id=uuid.uuid4())

    def test_get_owned_topic_rejects_other_users_topic(self):
        with self.assertRaises(NotFound):
            services.get_owned_topic(user=self.other, topic_id=self.topic.id)

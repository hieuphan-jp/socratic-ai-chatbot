"""
apps/topics/serializers.py

JA: JSONの形の定義と入力検証のみ。保存処理・業務判断は services.py の責務。
VI: Chỉ định nghĩa hình dạng JSON và kiểm tra đầu vào. Lưu/phán đoán nghiệp vụ
    thuộc trách nhiệm của services.py.
"""

from rest_framework import serializers

from .models import KnowledgeNode, Topic


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ["id", "user", "parent", "name", "description", "position", "created_at"]
        # JA: user/position はサーバが決める → read_only / VI: user/position do server quyết → read_only
        read_only_fields = ["id", "user", "position", "created_at"]


class KnowledgeNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeNode
        fields = ["id", "topic", "title", "content", "created_at"]
        read_only_fields = ["id", "created_at"]



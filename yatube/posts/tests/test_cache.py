from django.test import Client, TestCase
from django.core.cache import cache
from django.urls import reverse
from ..models import Post, User


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="NoName")
        cls.URL = reverse('posts:index')

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(CacheTests.user)

    def test_index_cache(self):
        self.post = Post.objects.create(
            text='Тестовый текст',
            author=self.user,
        )
        response = self.authorized_client.get('/')
        resp1 = response.content
        self.post.delete()
        response = self.authorized_client.get('/')
        resp2 = response.content
        self.assertEqual(
            resp1,
            resp2,
            'Кэширование не работает 1'
        )
        cache.clear()
        response = self.authorized_client.get('/')
        resp3 = response.content
        self.assertNotEqual(
            resp1,
            resp3,
            'Кэширование не работает 2'
        )

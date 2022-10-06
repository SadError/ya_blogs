from django.test import Client, TestCase
from django.urls import reverse
from ..models import Post, User, Follow
from django.contrib.auth import get_user_model

User = get_user_model()


class FollowerTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="TestFollower")
        cls.user_2 = User.objects.create_user(username="TestNotFollower")
        cls.author = User.objects.create_user(username="TestAuthor")
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )

    def setUp(self):
        self.authorized_follower = Client()
        self.authorized_follower.force_login(FollowerTests.user)

        self.authorized_author = Client()
        self.authorized_author.force_login(FollowerTests.author)

        self.authorized_user = Client()
        self.authorized_user.force_login(FollowerTests.user_2)

    def test_can_follow(self):
        """Авторизованный пользователь может подписываться на других"""
        self.authorized_follower.get(
            reverse(
                'posts:profile_follow', kwargs={
                    'username': self.author
                }
            )
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.user, author=self.author
            ).exists(),
        )

    def test_can_unfollow(self):
        '''Авторизованный пользователь может отписываться от других'''
        Follow.objects.create(
            user=self.user,
            author=self.author
        )
        self.authorized_follower.get(
            reverse(
                'posts:profile_unfollow', kwargs={
                    'username': self.author
                }
            )
        )
        self.assertFalse(
            Follow.objects.filter(
                user=self.user, author=self.author
            ).exists(),
        )

    def test_newpost_for_follower(self):
        '''Новый пост появляется у подписчиков автора
        и не появляется у остальных'''
        Follow.objects.create(
            user=self.user,
            author=self.author
        )
        response = self.authorized_follower.get('/follow/')
        resp1 = response.content
        response = self.authorized_user.get('/follow/')
        resp2 = response.content
        self.assertNotEqual(
            resp1,
            resp2,
        )

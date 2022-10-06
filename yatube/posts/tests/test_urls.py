from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from ..models import Group, Post
from http import HTTPStatus

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_exists_at_desired_location(self):
        """Общедоступные страницы сайта"""
        urls_response = {
            '/': HTTPStatus.OK,
            '/group/test-slug/': HTTPStatus.OK,
            '/profile/testuser/': HTTPStatus.OK,
            f'/posts/{self.post.pk}/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND
        }
        for url, status_code in urls_response.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status_code)

    # Проверяем доступность страниц для авторизованного пользователя
    def test_task_detail_url_exists_at_desired_location_authorized(self):
        response = self.authorized_client.get(f'/posts/{self.post.pk}/edit/')
        self.assertEqual(response.status_code, 200)

    def test_task_list_url_exists_at_desired_location(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, 200)

        # Проверяем редиректы для неавторизованного пользователя
    def test_edit_list_url_redirect_anonymous_on_login(self):
        response = self.guest_client.get(
            f'/posts/{self.post.pk}/edit/', follow=True
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.pk}/edit/')

    def test_create_list_url_redirect_anonymous_on_login(self):
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/')

        # Проверка вызываемых шаблонов для каждого адреса
    def test_urls_uses_correct_template(self):
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/testuser/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from ..models import Post, Group, User, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="NoName")
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )
        cls.comment = Comment.objects.create(
            text='Коммент',
            author=cls.user,
            post=cls.post
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.post_count = Post.objects.count()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsCreateFormTests.user)

    def test_post_create_form(self):
        """Тест создания нового поста в базе данных"""

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Текст теста заполнения форм',
            'author': PostsCreateFormTests.user,
            'group': PostsCreateFormTests.group.id,
            'image': uploaded
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        response_comment = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        comments_count = Comment.objects.count()
        post_latest = Post.objects.latest('pk')
        self.assertRedirects(response_comment, '/auth/login/?next=/create/')
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertEqual(Post.objects.count(), self.post_count + 1)
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': post_latest.author})
        )
        self.assertTrue(
            Post.objects.filter(
                image='posts/small.gif'
            ).exists()
        )
        self.assertEqual(post_latest.text, form_data['text'])
        self.assertEqual(post_latest.group.id, form_data['group'])
        self.assertEqual(post_latest.author, form_data['author'])

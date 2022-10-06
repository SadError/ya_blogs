from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Post, Group
from posts.utils import POSTS_ON_PAGE
from django.core.cache import cache


User = get_user_model()


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testman')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )
        cls.post_id = cls.post.id

    def setUp(self):
        cache.clear()
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_page_uses_correct_templates(self):
        '''Проверяем, что используються правильные шаблоны'''
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': 'test-slug'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': self.user}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post_id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post_id}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_correct_context(self):
        """ Проверяем, что в index передается правильный контекст:
        1. В context есть page_obj.
        2. Размер списка не равен нулю.
        """
        response = self.guest_client.get(reverse('posts:index'))
        self.assertIn('page_obj', response.context.keys())
        self.assertNotEqual(len(response.context['page_obj']), 0)

    def test_group_list_page_correct_context(self):
        '''Проверяем, что в список постов передается правильный контекст '''
        response = self.guest_client.get(reverse('posts:group_list',
                                         kwargs={'slug': 'test-slug'}))
        self.assertEqual(response.context['group'], self.group)

    def test_profile_page_correct_context(self):
        '''Проверяем, что в profile передается правильный контекст'''
        response = self.authorized_client.get(reverse('posts:profile',
                                              kwargs={'username': self.user}))
        self.assertEqual(response.context['author'], self.post.author)

    def test_post_detail_page_correct_context(self):
        '''Проверяем, что в post_detail передается правильный контекст'''
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post_id})
        )
        self.assertEqual(response.context['post'].id, self.post_id)

    def test_post_edit_page_correct_context(self):
        '''Проверяем, что в post_edit передается правильный контекст'''
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post_id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_create_post_page_correct_context(self):
        '''Проверяем, что в create_post передается правильный контекст'''
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_paginator(self):
        '''Проверка работы Пагинатора'''
        post = []
        for i in range(11):
            post.append(Post(
                text=f'Тестовый текст {post}',
                author=self.user,
                group=self.group,)
            )
        post = Post.objects.bulk_create(post)
        posturls_posts_page = [('', POSTS_ON_PAGE), ('?page=2', 2)]
        templates = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': self.user}),
        ]
        for postsurls, posts in posturls_posts_page:
            for page in templates:
                with self.subTest(page=page):
                    cache.clear()
                    response = self.authorized_client.get(page + postsurls)
                    self.assertEqual(len(response.context['page_obj']), posts)

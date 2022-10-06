from django.test import TestCase
from http import HTTPStatus


class ViewTestClass(TestCase):
    def test_error_page(self):
        response = self.client.get('/nonexist-page/')
        self.assertEqual(
            response.status_code, HTTPStatus.NOT_FOUND,
            'Проверьте, что статус ответа сервера - 404'
        )
        self.assertTemplateUsed(
            response, 'core/404.html',
            'Проверьте, что используется правильный шаблон'
        )

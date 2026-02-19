from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from news.models import News, Comment

User = get_user_model()


class TestRoutes(TestCase):
    """Тестирование доступности маршрутов."""

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель')
        cls.news = News.objects.create(
            title='Заголовок',
            text='Текст новости'
        )
        cls.comment = Comment.objects.create(
            news=cls.news,
            author=cls.author,
            text='Комментарий автора'
        )

    def test_home_availability(self):
        url = reverse('news:home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_detail_availability(self):
        url = reverse('news:detail', args=(self.news.pk,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_edit_delete_availability_for_author(self):
        self.client.force_login(self.author)
        edit_url = reverse('news:edit', args=(self.comment.pk,))
        delete_url = reverse('news:delete', args=(self.comment.pk,))
        response_edit = self.client.get(edit_url)
        response_delete = self.client.get(delete_url)
        self.assertEqual(response_edit.status_code, 200)
        self.assertEqual(response_delete.status_code, 200)

    def test_anonymous_redirect_for_edit_delete(self):
        edit_url = reverse('news:edit', args=(self.comment.pk,))
        delete_url = reverse('news:delete', args=(self.comment.pk,))
        login_url = reverse('users:login')
        expected_edit_redirect = f'{login_url}?next={edit_url}'
        expected_delete_redirect = f'{login_url}?next={delete_url}'

        response_edit = self.client.get(edit_url)
        response_delete = self.client.get(delete_url)

        self.assertRedirects(
            response_edit,
            expected_edit_redirect,
            status_code=302,
            target_status_code=200
        )
        self.assertRedirects(
            response_delete,
            expected_delete_redirect,
            status_code=302,
            target_status_code=200
        )

    def test_404_for_foreign_comment(self):
        self.client.force_login(self.reader)
        edit_url = reverse('news:edit', args=(self.comment.pk,))
        delete_url = reverse('news:delete', args=(self.comment.pk,))
        response_edit = self.client.get(edit_url)
        response_delete = self.client.get(delete_url)
        self.assertEqual(response_edit.status_code, 404)
        self.assertEqual(response_delete.status_code, 404)

    def test_login_signup_pages_availability(self):
        urls = [
            reverse('users:login'),
            reverse('users:signup'),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_logout_page_availability(self):
        url = reverse('users:logout')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

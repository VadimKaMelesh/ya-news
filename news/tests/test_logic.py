from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from news.models import News, Comment
from news.forms import BAD_WORDS, WARNING

User = get_user_model()


class TestCommentLogic(TestCase):
    """Проверка логики работы с комментариями."""

    @classmethod
    def setUpTestData(cls):
        """Создание данных для всех тестов класса."""
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

    def test_anonymous_cannot_post_comment(self):
        """
        Анонимный пользователь не может отправить комментарий.
        """
        url = reverse('news:detail', args=(self.news.pk,))
        comment_text = 'Пробный комментарий'
        response = self.client.post(url, data={'text': comment_text})
        expected_redirect = reverse('users:login') + '?next=' + url
        self.assertRedirects(
            response,
            expected_redirect,
            status_code=302,
            target_status_code=200
        )
        self.assertEqual(Comment.objects.count(), 1)

    def test_authorized_can_post_comment(self):
        """
        Авторизованный пользователь может отправить комментарий.
        """
        self.client.force_login(self.author)
        url = reverse('news:detail', args=(self.news.pk,))
        comment_text = 'Новый комментарий'
        response = self.client.post(url, data={'text': comment_text})
        expected_url = reverse('news:detail', 
                               args=(self.news.pk,)) + '#comments'
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)
        self.assertEqual(Comment.objects.count(), 2)
        new_comment = Comment.objects.exclude(pk=self.comment.pk).first()
        self.assertEqual(new_comment.text, comment_text)
        self.assertEqual(new_comment.news, self.news)
        self.assertEqual(new_comment.author, self.author)

    def test_cannot_post_comment_with_bad_words(self):
        """
        Если комментарий содержит запрещённые слова, он не публикуется,
        форма возвращает ошибку.
        """
        self.client.force_login(self.author)
        url = reverse('news:detail', args=(self.news.pk,))
        bad_text = f'Этот {BAD_WORDS[0]} текст'
        response = self.client.post(url, data={'text': bad_text})
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        form = response.context['form']
        self.assertIn('text', form.errors)
        self.assertIn(WARNING, form.errors['text'])
        self.assertEqual(Comment.objects.count(), 1)

    def test_author_can_edit_own_comment(self):
        """
        Авторизованный пользователь может редактировать свой комментарий.
        """
        self.client.force_login(self.author)
        edit_url = reverse('news:edit', args=(self.comment.pk,))
        new_text = 'Обновлённый текст'
        response = self.client.post(edit_url, data={'text': new_text})
        expected_url = reverse('news:detail',
                               args=(self.news.pk,)) + '#comments'
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.text, new_text)

    def test_author_can_delete_own_comment(self):
        """
        Авторизованный пользователь может удалить свой комментарий.
        """
        self.client.force_login(self.author)
        delete_url = reverse('news:delete', args=(self.comment.pk,))
        response = self.client.post(delete_url)
        expected_url = reverse('news:detail',
                               args=(self.news.pk,)) + '#comments'
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)
        self.assertEqual(Comment.objects.count(), 0)

    def test_user_cannot_edit_foreign_comment(self):
        """
        Авторизованный пользователь не может редактировать чужой комментарий.
        """
        self.client.force_login(self.reader)
        edit_url = reverse('news:edit', args=(self.comment.pk,))
        response_get = self.client.get(edit_url)
        self.assertEqual(response_get.status_code, 404)
        response_post = self.client.post(edit_url, data={'text': 'Новый текст'})
        self.assertEqual(response_post.status_code, 404)
        self.comment.refresh_from_db()
        self.assertNotEqual(self.comment.text, 'Новый текст')

    def test_user_cannot_delete_foreign_comment(self):
        """
        Авторизованный пользователь не может удалить чужой комментарий.
        """
        self.client.force_login(self.reader)
        delete_url = reverse('news:delete', args=(self.comment.pk,))
        response_get = self.client.get(delete_url)
        self.assertEqual(response_get.status_code, 404)
        response_post = self.client.post(delete_url)
        self.assertEqual(response_post.status_code, 404)
        self.assertTrue(Comment.objects.filter(pk=self.comment.pk).exists())

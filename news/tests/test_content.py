from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from news.models import News, Comment

User = get_user_model()


class TestContent(TestCase):
    """Проверка содержимого страниц."""

    @classmethod
    def setUpTestData(cls):
        """Создание данных для всех тестов класса."""
        today = timezone.now().date()
        cls.news_list = []
        for i in range(15):
            news = News.objects.create(
                title=f'Новость {i}',
                text=f'Текст {i}',
                date=today - timedelta(days=i)
            )
            cls.news_list.append(news)

        cls.news_for_comments = cls.news_list[0]
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель')

        now = timezone.now()
        for i in range(3):
            Comment.objects.create(
                news=cls.news_for_comments,
                author=cls.author if i % 2 == 0 else cls.reader,
                text=f'Комментарий {i}',
                created=now + timedelta(minutes=i)
            )

    def test_news_count_on_homepage(self):
        """
        Количество новостей на главной странице — не более 10.
        """
        url = reverse('news:home')
        response = self.client.get(url)
        self.assertIn('news_list', response.context)
        news_on_page = response.context['news_list']
        self.assertEqual(len(news_on_page), 10)

    def test_news_order_on_homepage(self):
        """
        Новости отсортированы от самой свежей к самой старой.
        Свежие новости в начале списка.
        """
        url = reverse('news:home')
        response = self.client.get(url)
        news_on_page = response.context['news_list']
        dates = [news.date for news in news_on_page]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_comments_order_on_detail_page(self):
        """
        Комментарии на странице отдельной новости отсортированы
        от старых к новым: старые в начале, новые в конце.
        """
        url = reverse('news:detail', args=(self.news_for_comments.pk,))
        response = self.client.get(url)
        self.assertIn('news', response.context)
        news_obj = response.context['news']
        comments = list(news_obj.comment_set.all())
        created_times = [c.created for c in comments]
        self.assertEqual(created_times, sorted(created_times))

    def test_comment_form_not_available_for_anonymous(self):
        """
        Анонимному пользователю недоступна форма для отправки комментария.
        """
        url = reverse('news:detail', args=(self.news_for_comments.pk,))
        response = self.client.get(url)
        self.assertNotIn('form', response.context)

    def test_comment_form_available_for_authorized(self):
        """
        Авторизованному пользователю доступна форма для отправки комментария.
        """
        self.client.force_login(self.author)
        url = reverse('news:detail', args=(self.news_for_comments.pk,))
        response = self.client.get(url)
        self.assertIn('form', response.context)

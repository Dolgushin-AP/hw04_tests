from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


CHAR_LIMIT = 15


class Group(models.Model):
    """ Модель для сообществ """
    title = models.CharField(
        verbose_name='Название группы',
        max_length=200,
        help_text='Введите название группы',
    )
    slug = models.SlugField(
        verbose_name='Связанная ссылка',
        max_length=100,
        unique=True,
        help_text='Введите адрес ссылки',
    )
    description = models.TextField(
        verbose_name='Описание группы',
        help_text='Введите описание',
    )

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

    def __str__(self):
        """ При печати объекта модели Group выводится поле title """
        return f"{self.title}"


class Post(models.Model):
    """ Модель для постов """
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name='Группа',
        related_name='posts',
        help_text='Выберите группу из списка или создайте новую',
    )
    text = models.TextField(
        verbose_name='Текст поста',
        help_text='Введите текст поста',
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
        help_text='Заполняется автоматически',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='posts',
        help_text='Выберите автора из списка или создайте нового',
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:CHAR_LIMIT]

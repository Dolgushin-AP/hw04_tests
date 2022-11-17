from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


CHAR_LIMIT = 15


class Group(models.Model):
    """ Модель для сообществ """
    title = models.CharField(verbose_name='Название группы', max_length=200)
    slug = models.SlugField(verbose_name='Связанная ссылка',
                            max_length=100, unique=True)
    description = models.TextField(verbose_name='Описание группы')

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
        related_name='posts'
    )
    text = models.TextField(verbose_name='Текст поста')
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='posts'
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:CHAR_LIMIT]

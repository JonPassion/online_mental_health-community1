from django.db import models
from django.conf import settings

class Post(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=150)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.author.username} on "{self.post.title}"'


REACTION_CHOICES = [
    ('like',  '👍'),
    ('love',  '❤️'),
    ('haha',  '😂'),
    ('wow',   '😮'),
    ('sad',   '😢'),
    ('angry', '😡'),
]

class Reaction(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=10, choices=REACTION_CHOICES)

    class Meta:
        unique_together = ['post', 'user']

    def __str__(self):
        return f'{self.user.username} {self.reaction_type} "{self.post.title}"'

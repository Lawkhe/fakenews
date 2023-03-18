from django.db import models

class Rol(models.Model):
    name = models.CharField(max_length=20)
    description = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=50)
    password = models.CharField(max_length=200)
    rol = models.ForeignKey(
        Rol, on_delete=models.CASCADE
    )
    state = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Type(models.Model):
    name = models.CharField(max_length=50)
    state = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
class Origin(models.Model):
    name = models.CharField(max_length=50)
    state = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class News(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE
    )
    title = models.CharField(max_length=50)
    type = models.ForeignKey(
        Type, on_delete=models.CASCADE
    )
    origin = models.ForeignKey(
        Origin, on_delete=models.CASCADE
    )
    public = models.BooleanField(default=False)
    percentage = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField()
    state = models.BooleanField(default=True)

    def __str__(self):
        return self.state
    
class Score(models.Model):
    news = models.ForeignKey(
        News, on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE
    )
    score = models.IntegerField()
    state = models.BooleanField(default=True)

    def __str__(self):
        return self.score

class Media(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

def content_directory_path(instance, filename):
    return 'static/upload/content/{0}/{1}'.format(instance.news.id, filename)

class Content(models.Model):
    news = models.ForeignKey(
        News, on_delete=models.CASCADE
    )
    media = models.ForeignKey(
        Media, on_delete=models.CASCADE
    )
    data = models.TextField()
    file_path = models.FileField(upload_to=content_directory_path, null=True, blank=True)
    result = models.TextField()

    def __str__(self):
        return self.result

class Traceability(models.Model):
    content = models.ForeignKey(
        Content, on_delete=models.CASCADE
    )
    action = models.CharField(max_length=30)
    description = models.TextField()

    def __str__(self):
        return self.description

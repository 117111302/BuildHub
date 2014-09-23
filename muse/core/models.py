from django.db import models


class Repo(models.Model):
    repo_id = models.IntegerField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    enable = models.BooleanField(default=False)


class Payload(models.Model):
    repo_id = models.CharField(max_length=30)
    name = models.CharField(max_length=255)
    build_id = models.CharField(max_length=30)
    branch = models.CharField(max_length=255)
    message = models.CharField(max_length=255)
    commit = models.CharField(max_length=255)
    committer = models.CharField(max_length=255)
    start = models.DateTimeField(auto_now_add=True)
    end = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('repo_id', 'commit')

    def __unicode__(self):
        return '(%d, %s)' % (self.id, self.name)


class Badge(models.Model):
    repo = models.CharField(max_length=255)
    branch = models.CharField(max_length=255)
    status = models.CharField(max_length=30, default='SUCCESS')

    class Meta:
        unique_together = ('repo', 'branch', 'status')

    def __unicode__(self):
        return '(%s, %s)' % (self. repo, self.status)

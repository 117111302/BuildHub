from django.db import models

# Create your models here.
class Payload(models.Model):
    repo = models.CharField(max_length=30)
    payload = models.TextField()
    build_id = models.CharField(max_length=30)

    def __unicode__(self):
	return '(%d, %s)' % (self.id, self.repo)


class Badge(models.Model):
    repo = models.CharField(max_length=30)
    branch = models.CharField(max_length=30)
    status = models.CharField(max_length=30, default='SUCCESS')

    def __unicode__(self):
        return '(%s, %s)' % (self. repo, self.status)

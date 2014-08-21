from django.db import models

# Create your models here.
class Payload(models.Model):
    repo = models.CharField(max_length=30)
    payload = models.TextField()

    def __unicode__(self):
	return '(%d, %s)' % (self.id, self.repo)

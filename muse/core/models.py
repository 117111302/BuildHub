from django.db import models

# Create your models here.
class Webhook(models.Model):
    repo = models.CharField(max_length=30)
    event = models.CharField(max_length=30)
    payload = models.TextField()

    def __unicode__(self):
	return self.repo + self.event

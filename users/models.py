from django.contrib.auth.models import User
from django.db import models
from taggit.managers import TaggableManager


class UserInOutInfo(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	date = models.DateField(auto_now=False, auto_now_add=False)
	title = models.CharField(max_length=100)
	operation_type = models.CharField(max_length=10, choices=(('income', 'income'), ('expense', 'expense')))
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	created_at = models.DateTimeField(auto_now_add=True)
	tag = TaggableManager()

	class Meta:
		ordering = ['-date']
		verbose_name = 'User In-Out'
		verbose_name_plural = 'Users In-Out'
		app_label = 'users'

	def __str__(self):
		return self.title
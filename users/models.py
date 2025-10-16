from django.contrib.auth.models import User
from django.db import models
from django.utils.text import slugify


class UserInOutInfo(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	date = models.DateField(auto_now=False, auto_now_add=False)
	title = models.CharField(max_length=100)
	operation_type = models.CharField(max_length=10, choices=(('income', 'income'), ('expense', 'expense')))
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	tag = models.ForeignKey('OperationTags', on_delete=models.CASCADE, null=True, blank=True, default=1, related_name='tags', verbose_name='tag')

	class Meta:
		ordering = ['-date']
		verbose_name = 'User In-Out'
		verbose_name_plural = 'Users In-Out'
		app_label = 'users'

	def __str__(self):
		return self.title


class OperationTags(models.Model):
	tag = models.CharField(max_length=100, unique=True, verbose_name='tag')
	slug = models.SlugField(max_length=100, unique=True)
	svg = models.TextField(max_length=100, blank=True, default='', verbose_name='svg')

	def __str__(self):
		return self.tag

	def save(self, *args, **kwargs):
		if self.pk and self.tag != self.objects.get(pk=self.pk).tag:
			self.slug = slugify(self.tag)

		if not self.slug:
			self.slug = slugify(self.tag)
			self.save()
		super(OperationTags, self).save(*args, **kwargs)
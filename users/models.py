from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings

class User(AbstractUser):
	SUBSCRIPTION_CHOICES = [
		('free', 'Free'),
		('pro', 'Pro'),
	]
	subscription_tier = models.CharField(max_length=10, choices=SUBSCRIPTION_CHOICES, default='free')
	reports_this_month = models.PositiveIntegerField(default=0)
	last_report_reset = models.DateField(null=True, blank=True)

	def refresh_monthly_usage(self):
		today = timezone.now().date()
		if self.last_report_reset is None:
			self.last_report_reset = today
			self.save(update_fields=['last_report_reset'])
			return

		if (
			self.last_report_reset.year != today.year
			or self.last_report_reset.month != today.month
		):
			self.reports_this_month = 0
			self.last_report_reset = today
			self.save(update_fields=['reports_this_month', 'last_report_reset'])

	def can_create_report(self):
		self.refresh_monthly_usage()
		if self.subscription_tier == 'pro':
			return True
		return self.reports_this_month < settings.FREE_TIER_MONTHLY_REPORT_LIMIT

	def increment_report_usage(self):
		self.refresh_monthly_usage()
		self.reports_this_month += 1
		self.last_report_reset = timezone.now().date()
		self.save(update_fields=['reports_this_month', 'last_report_reset'])

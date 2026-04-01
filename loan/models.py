from datetime import datetime
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class MainLoan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    loan_type = models.CharField(max_length=50, choices=(
        ('Mortgage', 'Mortgage'), ('Loan', 'Loan'), ('Other', 'Other'), ('Installment', 'Installment'),
    ), null=False, blank=False)
    loan_name = models.CharField(max_length=50, null=False, blank=False)
    color = models.CharField(max_length=50, null=True, blank=False, default='#ffffff')
    icon = models.ForeignKey('LoanSVG', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='icon')
    down_payment = models.DecimalField(max_digits=12, decimal_places=2, default=None, null=True, blank=True)
    property_value = models.DecimalField(max_digits=12, decimal_places=2, default=None, null=True, blank=True)
    loan_amount = models.DecimalField(max_digits=12, decimal_places=2, default=None, null=False, blank=False)
    interest_rate = models.DecimalField(max_digits=4, decimal_places=1, default=None, null=True, blank=True)
    loan_term = models.PositiveIntegerField(default=None, null=False, blank=False)
    loan_insurance = models.DateField(null=False, blank=False, default=None)
    loan_end = models.DateField(null=False, blank=False, default=None)
    monthly_payment = models.DecimalField(max_digits=12, decimal_places=2, default=None, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(auto_now=True)
    commission = models.DecimalField(max_digits=12, decimal_places=2, default=None, null=True, blank=True)
    comment = models.CharField(max_length=100, default=None, null=True, blank=True)
    active = models.BooleanField(default=True, null=False, blank=False)

    def __str__(self):
        return self.loan_name

    class Meta:
        db_table = 'Loan'
        ordering = ['-created_at', '-edited_at', 'user']
        indexes = [
            models.Index(fields=['loan_type', 'loan_name']),
            models.Index(fields=['comment', 'loan_name']),
        ]
        unique_together = (('loan_name', 'user'),)

    def save(self, *args, **kwargs):
        if self.loan_end and self.loan_insurance:
            self.loan_term = (self.loan_end - self.loan_insurance).days // 31
        elif self.down_payment and self.property_value:
            self.loan_amount = self.property_value - self.down_payment
        super().save(*args, **kwargs)


class LoanDetail(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    loan = models.ForeignKey(MainLoan, on_delete=models.CASCADE)
    title = models.CharField(max_length=50, null=True, blank=False,
                             default=f'payment for {datetime.now().strftime("%d-%m-%Y")}')
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=None, null=True, blank=True)

    class Meta:
        db_table = 'Loan_Detail'


class LoanSVG(models.Model):
    icon = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'Loan_SVG'
from django.db import models


class Hazard(models.Model):
    HAZARD_TYPE_CHOICES = [
        ('BLACKSPOT', 'Black Spot'),
        ('BAD_ROAD', 'Bad Road'),
        ('ACCIDENT', 'Accident'),
        ('PEDESTRIANS', 'Pedestrians'),
    ]

    SEVERITY_CHOICES = [(i, str(i)) for i in range(1, 6)]

    type = models.CharField(max_length=20, choices=HAZARD_TYPE_CHOICES)
    latitude = models.FloatField()
    longitude = models.FloatField()
    severity = models.IntegerField(choices=SEVERITY_CHOICES)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_type_display()} - ({self.latitude}, {self.longitude})"

    class Meta:
        ordering = ['-created_at']


class Report(models.Model):
    phone_number = models.CharField(max_length=20)
    hazard_type = models.CharField(max_length=20, choices=Hazard.HAZARD_TYPE_CHOICES)
    latitude = models.FloatField()
    longitude = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report from {self.phone_number} - {self.get_hazard_type_display()}"

    class Meta:
        ordering = ['-created_at']


class AlertLog(models.Model):
    CHANNEL_CHOICES = [
        ('SMS', 'SMS'),
        ('VOICE', 'Voice'),
    ]

    phone_number = models.CharField(max_length=20)
    hazard = models.ForeignKey(Hazard, on_delete=models.CASCADE, related_name='alerts')
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES)
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Alert to {self.phone_number} via {self.get_channel_display()}"

    class Meta:
        ordering = ['-sent_at']

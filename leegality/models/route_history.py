from django.db import models


class RouteHistory(models.Model):
    STATUS_SUCCESS = 'success'
    STATUS_ERROR = 'error'
    STATUS_CHOICES = [
        (STATUS_SUCCESS, 'Success'),
        (STATUS_ERROR, 'Error'),
    ]

    id = models.AutoField(primary_key=True)
    source = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    latency = models.FloatField(null=True, blank=True)
    path = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=7, choices=STATUS_CHOICES)
    message = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'route_history'

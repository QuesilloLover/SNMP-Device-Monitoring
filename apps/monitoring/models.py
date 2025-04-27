from django.db import models

class Device(models.Model):
    """
    Stores basic SNMP connection info for a network device.
    """
    
    name = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField()
    port = models.PositiveIntegerField(default=161)
    community = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.ip_address})"

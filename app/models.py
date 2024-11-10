from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

# Create your models here.
# tạo form đăng kí
class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

# bảng dữ liệu snapshot
from django.db import models

class SnapshotList(models.Model):
    id = models.AutoField(primary_key=True)
    time = models.TimeField()
    event = models.CharField(max_length=50, default='Chụp hình')
    image_url = models.CharField(max_length=255)
    end_time = models.TimeField()
    camera = models.IntegerField()
    date = models.DateField()

    class Meta:
        db_table = 'app_snapshotlist'  # Đảm bảo ánh xạ đúng tên bảng trong MySQL

    def __str__(self):
        return f"{self.date} - {self.event} at {self.time}"

class Camera(models.Model):
    PROTOCOL_CHOICES = [
        ('http', 'HTTP'),
        ('https', 'HTTPS'),
        ('rtsp', 'RTSP'),
    ]

    name = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(protocol='both', unpack_ipv4=True, blank=True, null=True)
    port = models.IntegerField(blank=True, null=True)
    protocol = models.CharField(max_length=10, choices=PROTOCOL_CHOICES, default='rtsp')
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    stream_name = models.CharField(max_length=100, blank=True, null=True)
    account = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = 'camera'

    def __str__(self):
        return self.name

    def get_stream_url(self):
        """Phương thức tạo URL stream dựa trên giao thức."""
        if self.protocol == 'rtsp':
            # URL RTSP yêu cầu username, password và có thể có stream_name
            return f'rtsp://{self.username}:{self.password}@{self.ip_address}:{self.port}/{self.stream_name}'
        elif self.protocol in ['http', 'https']:
            # URL HTTP/HTTPS có thể hoặc không cần username, password và stream_name
            auth = f'{self.username}:{self.password}@' if self.username and self.password else ''
            return f'{self.protocol}://{auth}{self.ip_address}:{self.port}/{self.stream_name}'
        return None


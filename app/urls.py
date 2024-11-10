from django.contrib import admin
from django.urls import path, include
from . import views
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    path('', views.get_home, name = "home"),
    path('login/', views.dangNhap, name = "login"),
    path('logout/', views.logoutPage, name = "logout"),
    path('register/', views.dangKi, name = "register"),
    path('new-camera/', views.newcamera, name = "new-camera"),   # chuyển link sang thêm camera
    path('add-camera/', views.add_camera, name='add-camera'), 
    path('get-timeline-data/', views.get_timeline_data, name='get_timeline_data'), # lấy dữ liệu các ảnh trong ngày được chọn
    path('upload_image/', views.upload_image, name='upload_image'),             # lưu ảnh vào thư mục và thêm vào cơ sở dữ liệu
    path('snapshot/', views.show_snapshot, name = "snapshot"),                  # hiển thị ảnh
    path('select-camera/<int:camera_id>/', views.select_camera, name='select-camera'),
    path('camera/<int:camera_id>/', views.camera_detail, name='camera_detail'),       # chứa thông tin camera
    path('camera-feed/<int:camera_id>/', views.stream_camera, name='stream_camera'),  # chứa hình ảnh camera
    path('delete-snapshot/', views.delete_snapshot, name='delete_snapshot'),    # xóa ảnh trong thư mục và cơ sở dữ liệu
    path('create-new-camera/', views.new_camera, name='create-new-camera'),  # thêm mới camera vào cơ sở dữ liệu
]

if settings.DEBUG:
    # urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
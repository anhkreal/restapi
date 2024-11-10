from django.forms import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, FileResponse, Http404, StreamingHttpResponse
import requests
from .models import *
import json
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.http import require_GET
import datetime
from .models import SnapshotList
import base64
import os
from django.conf import settings
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
import cv2  # Thư viện OpenCV để xử lý RTSP
import re
from django.views.decorators.http import require_POST

# Create your views here.
def get_home(request): 
    return render(request, 'home.htm') 

def dangKi(request): 
    form = CreateUserForm()
    context = {'form':form}
    if request.method == "POST":
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
    return render(request, 'register.htm', context) 

def dangNhap(request): 
    #if request.user.is_authenticated:
     #   return redirect('login')
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username = username, password = password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.info(request, 'Kiểm tra lại tên tài khoản hoặc mật khẩu')
    context = {}
    return render(request, 'login.htm', context) 

def logoutPage(request):
    logout(request)
    return redirect('login')

@login_required
def newcamera(request):
    return render(request, 'new-camera.htm') 

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Camera


@login_required
def add_camera(request):
    if request.method == 'POST':
        name = request.POST['name']
        ip_address = request.POST['ip_address']
        port = request.POST['port']
        protocol = request.POST['protocol']
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')  # Sử dụng '' nếu không có mật khẩu
        stream_name = request.POST.get('stream_name', '')

        # Tạo camera mới
        camera = Camera(
            name=name,
            ip_address=ip_address,
            port=port,
            protocol=protocol,
            username=username,
            password=password,
            stream_name=stream_name,
            account=request.user
        )
        camera.save()
        
        # Chuyển hướng về trang new-camera
        return redirect('new-camera')  

    return render(request, 'new-camera.htm')

import datetime
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from .models import SnapshotList  # Giả sử SnapshotList là model chứa dữ liệu

@login_required
@require_GET
def get_timeline_data(request):
    date_str = request.GET.get('date')
    camera_id = request.GET.get('id')  # Lấy camera_id từ tham số yêu cầu

    if not date_str:
        return JsonResponse({'error': 'Thiếu tham số ngày.'}, status=400)

    try:
        selected_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Định dạng ngày không hợp lệ. Vui lòng sử dụng YYYY-MM-DD.'}, status=400)

    # Truy xuất dữ liệu từ cơ sở dữ liệu MySQL, lọc theo ngày và camera_id
    if camera_id:  # Kiểm tra nếu camera_id được cung cấp
        snapshots = SnapshotList.objects.filter(date=selected_date, camera=camera_id).order_by('time')
    else:
        snapshots = SnapshotList.objects.filter(date=selected_date).order_by('time')

    if not snapshots.exists():
        return JsonResponse({'events': []})

    timeline_data = {}

    # Chuyển đổi dữ liệu truy xuất được thành định dạng mong muốn
    for snapshot in snapshots:
        event_time = snapshot.time.strftime('%H:%M:%S')
        event_date_str = snapshot.date.strftime('%Y-%m-%d')

        event = {
            "time": event_time,
            "event": snapshot.event,
            "image_url": snapshot.image_url,  # có thể cần xử lý URL ảnh nếu cần
            "camera": snapshot.camera,  # Đây sẽ là ID camera
            "date": event_date_str,
        }

        if event_date_str not in timeline_data:
            timeline_data[event_date_str] = []

        timeline_data[event_date_str].append(event)

    data = timeline_data.get(date_str, [])
    return JsonResponse({'events': data})


@login_required
@csrf_protect
def upload_image(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            image_data = data.get('image')
            event = data.get('event', 'Chụp hình')  # Lấy thông tin sự kiện từ frontend hoặc đặt mặc định
            camera = data.get('camera', select_camera.id)  # Lấy thông tin camera từ frontend hoặc đặt mặc định

            if not image_data:
                return JsonResponse({'success': False, 'error': 'Không có dữ liệu hình ảnh'}, status=400)

            # Xử lý dữ liệu base64
            format, imgstr = image_data.split(';base64,') 
            ext = format.split('/')[-1]  # Lấy đuôi file (ví dụ: png)

            # Tạo tên file duy nhất
            now = datetime.datetime.now()
            timestamp = now.strftime("%H_%M_%S_%d_%m_%Y")
            file_name = f"snapshot_{timestamp}.{ext}"

            # Đường dẫn lưu trữ
            file_path = os.path.join(settings.MEDIA_ROOT, 'app', 'images', file_name)
            # file_path = os.path.join(settings.STATIC_URL, 'app', 'images', file_name)

            # Tạo thư mục nếu chưa tồn tại
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Giải mã base64 và lưu file
            with open(file_path, 'wb') as f:
                f.write(base64.b64decode(imgstr))

            # chỉ lưu tên file
            image_url = file_name

            # Tạo bản ghi mới trong SnapshotList
            snapshot = SnapshotList.objects.create(
                time=now.time(),
                event=event,
                image_url=image_url,  # Lưu đường dẫn đến hình ảnh
                end_time=now.time(),  # Vì là hình ảnh nên time = end_time
                camera=camera,
                date=now.date()
            )

            return JsonResponse({
                'success': True,
                'file_name': file_name,
                'image_url': image_url,
                'snapshot_id': snapshot.id
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Phương thức không được hỗ trợ'}, status=405)

def camera_detail(request, camera_id):
    camera = get_object_or_404(Camera, id=camera_id)
    
    # Tạo URL stream từ thông tin của camera
    stream_url = f"{camera.protocol}://{camera.username}:{camera.password}@{camera.ip_address}:{camera.port}/{camera.stream_name}"
    
    camera_online = False
    # Kiểm tra kết nối dựa trên giao thức
    if camera.protocol in ['http', 'https']:
        # Kiểm tra cho giao thức http/https
        try:
            response = requests.get(stream_url, timeout=5)
            response.raise_for_status()  # Kiểm tra nếu có lỗi HTTP
            camera_online = True
        except (requests.RequestException, requests.HTTPError):
            camera_online = False
    elif camera.protocol == 'rtsp':
        # Kiểm tra cho giao thức rtsp bằng OpenCV
        try:
            # Kiểm tra nếu RTSP URL hợp lệ (có dạng rtsp://...)
            if re.match(r'^rtsp://', stream_url):
                cap = cv2.VideoCapture(stream_url)
                if cap.isOpened():
                    camera_online = True
                cap.release()
        except Exception as e:
            print(f"Lỗi khi kết nối RTSP: {e}")
            camera_online = False

    # Trả về thông tin camera và trạng thái kết nối
    return render(request, 'home.htm', {
        'selected_camera': camera,
        'camera_online': camera_online
    })


def select_camera(request, camera_id):
    # Lấy camera đã chọn
    camera = get_object_or_404(Camera, id=camera_id)
    
    # Lưu thông tin camera vào session
    request.session['selected_camera'] = {
        'id': camera.id,
        'name': camera.name,
        'protocol': camera.protocol,
        'ip_address': camera.ip_address,
        'port': camera.port,
        'username': camera.username,
        'password': camera.password,
        'stream_name': camera.stream_name,
    }
    
    return redirect('home')  # Chuyển hướng về trang chủ hoặc trang mong muốn


def gen_frames(camera_url):
    cap = cv2.VideoCapture(camera_url)
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def stream_camera(request, camera_id):
    camera = get_object_or_404(Camera, id=camera_id)
    return StreamingHttpResponse(gen_frames(camera.get_stream_url()),
                                 content_type='multipart/x-mixed-replace; boundary=frame')


@login_required
@require_GET
def show_snapshot(request):
    url_str = request.GET.get('url')

    if not url_str:
        raise Http404("URL hoặc ID không tồn tại")

    # Lấy tên tệp từ đường dẫn
    file_name = os.path.basename(url_str)

    # Đường dẫn tới file thực tế
    file_path = os.path.join(settings.MEDIA_ROOT, 'app', 'images', file_name)

    # Kiểm tra file có tồn tại không
    if not os.path.exists(file_path):
        raise Http404("File không tồn tại")
    
    # Lưu cả URL đầy đủ và tên tệp vào session
    request.session['full_image_url'] = url_str  # URL đầy đủ
    request.session['selected_image_url'] = file_name  # chỉ tên tệp

    # Trả về ảnh dưới dạng FileResponse
    return FileResponse(open(file_path, 'rb'), content_type='image/jpeg')



@login_required
@require_POST
def delete_snapshot(request):
    full_image_url = request.POST.get('full_image_url')
    
    if not full_image_url:
        return JsonResponse({'error': 'URL không tồn tại'}, status=400)
    
    # Lấy tên tệp từ URL đầy đủ
    file_name = os.path.basename(full_image_url)

    # Đường dẫn thực tới file trong hệ thống
    file_path = os.path.join(settings.MEDIA_ROOT, 'app', 'images', file_name)
    
    try:
        # Xóa bản ghi trong cơ sở dữ liệu dựa trên URL ảnh
        snapshot = SnapshotList.objects.get(image_url=file_name)
        snapshot.delete()
        
        # Xóa file ảnh trong hệ thống nếu nó tồn tại
        if os.path.exists(file_path):
            os.remove(file_path)
        else:
            return JsonResponse({'error': 'File không tồn tại'}, status=404)
        
        return JsonResponse({'success': 'Ảnh đã được xóa thành công'})
    
    except SnapshotList.DoesNotExist:
        return JsonResponse({'error': 'Ảnh không tồn tại trong cơ sở dữ liệu'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@login_required
def new_camera(request):
    if request.method == 'POST':
        # Lấy dữ liệu từ form
        name = request.POST.get('name')
        ip_address = request.POST.get('ip_address')
        port = request.POST.get('port')
        protocol = request.POST.get('protocol')
        username = request.POST.get('username')
        password = request.POST.get('password')
        stream_name = request.POST.get('stream_name')

        # Kiểm tra dữ liệu đầu vào
        errors = {}
        if not name:
            errors['name'] = ["Tên camera không được để trống."]
        # ... (Các kiểm tra khác)

        if errors:
            return JsonResponse({'errors': errors}, status=400)

        # Tạo và lưu camera vào cơ sở dữ liệu
        camera = Camera(
            name=name,
            ip_address=ip_address,
            port=port,
            protocol=protocol,
            username=username,
            password=password,
            stream_name=stream_name,
            #account=request.user
            account=1
        )

        try:
            camera.save()
            return JsonResponse({'message': 'Camera đã được thêm thành công!'})
        except ValidationError as e:
            return JsonResponse({'errors': {'general': ['Có lỗi xảy ra khi lưu camera: ' + str(e)]}}, status=400)

    return render(request, 'new-camera.htm') 


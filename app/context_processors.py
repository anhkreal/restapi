from .models import Camera

# hàm lấy danh sách camera thuộc tài khoản
def camera_list_processor(request):
    if request.user.is_authenticated:  # Kiểm tra xem user đã đăng nhập chưa
        cameras = Camera.objects.filter(account=request.user)  # Lọc các camera thuộc về user
    else:
        cameras = []  # Nếu chưa đăng nhập, không có camera nào
    return {'cameras': cameras}  # Trả về context 'cameras'

# hàm lấy camera đang được chọn
def camera_info(request):
    # Kiểm tra nếu người dùng đã đăng nhập
    if request.user.is_authenticated:
        # Lấy thông tin camera từ session
        selected_camera = request.session.get('selected_camera', None)
    else:
        # Nếu chưa đăng nhập, không có thông tin camera
        selected_camera = None

    return {
        'selected_camera': selected_camera
    }

# hàm lấy hình ảnh đang hiển thị
def selected_image(request):
    full_image_url = request.session.get('full_image_url', None)  # URL đầy đủ
    image_url = request.session.get('selected_image_url', None)  # chỉ tên tệp
    
    return {
        'full_image_url': full_image_url,
        'selected_image_url': image_url,
    }

import torch
print(torch.cuda.is_available())  # 检查是否有可用的GPU
print(torch.cuda.current_device())  # 获取当前GPU的设备编号
print(torch.cuda.device_count())  # 检查GPU的数量
import torch

# 获取当前GPU的完整信息
gpu_info = torch.cuda.get_device_properties(0)
gpu_info_dict = {
    "name": gpu_info.name,
    "total_memory": gpu_info.total_memory / (1024 ** 2),
    "memory_allocated": torch.cuda.memory_allocated(0) / (1024 ** 2),  # 当前已分配的显存 (MB)
    "memory_cached": torch.cuda.memory_reserved(0) / (1024 ** 2),  # 当前缓存的显存 (MB)
    "multi_processor_count": gpu_info.multi_processor_count,
    "compute_capability": gpu_info.major,
    "driver_version": torch.__version__
}

print(gpu_info_dict)

# 获取当前GPU的完整信息
gpu_info1 = torch.cuda.get_device_properties(1)
gpu_info_dict1 = {
    "name": gpu_info1.name,
    "total_memory": gpu_info1.total_memory / (1024 ** 2),
    "memory_allocated": torch.cuda.memory_allocated(0) / (1024 ** 2),
    "memory_cached": torch.cuda.memory_reserved(0) / (1024 ** 2),
    "multi_processor_count": gpu_info1.multi_processor_count,
    "compute_capability": gpu_info1.major,
    "driver_version": torch.__version__
}

print(gpu_info_dict1)


from flask import Flask

app = Flask(__name__)

# 主页路由
@app.route('/')
def home():
    return "欢迎来到首页！"

# 显示一个欢迎信息
@app.route('/greet/<name>')
def greet(name):
    return f"你好，{name}！欢迎访问本网站！"

# 处理POST请求
@app.route('/submit', methods=['POST'])
def submit():
    return "数据已提交！"

# 处理GET请求
@app.route('/info', methods=['GET'])
def info():
    return "这是一个处理GET请求的路由！"

if __name__ == "__main__":
    app.run(debug=True)
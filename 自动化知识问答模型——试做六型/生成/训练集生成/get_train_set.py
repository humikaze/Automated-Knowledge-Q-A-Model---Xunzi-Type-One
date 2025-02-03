import random  # 导入随机数生成模块
import copy  # 导入深拷贝模块
import json  # 导入JSON模块，用于读取和写入JSON文件

# 根据描述获取相关身份
def get_identity(desc):
    for identity in title_identities:  # 遍历所有身份
        if identity in desc:  # 如果身份在描述中出现
            return identity  # 返回该身份
    return None  # 如果没有匹配的身份，返回None

# 读取title_identities.txt文件中的内容并去除空格
with open("title_identities.txt", encoding="utf-8") as f:
    title_identities = [s.strip() for s in f.readlines()]

# 读取knowledge.json文件中的内容
with open("knowledge.json", encoding="utf-8") as f:
    lines = f.readlines()

# 初始化存储身份描述的字典
identity_desc = {}

# 解析JSON文件中的每一行数据
data = [json.loads(line.strip()) for line in lines]

# 提取所有描述
all_desc = [item["Q"] for item in data if "Q" in item]

# 遍历所有数据项，将相同身份的描述合并到一起
for s in data:
    desc = s["Q"]
    identity = get_identity(desc)  # 获取描述中的身份
    if identity not in identity_desc:  # 如果字典中没有该身份
        identity_desc[identity] = []  # 初始化该身份的描述列表
    identity_desc[identity].append(desc)  # 将描述添加到身份对应的列表中

# 初始化正负样本数据列表
pos_data = []
neg_data = []

count = 0  # 计数器
# 遍历所有身份及其对应的描述列表
for key, value_list in identity_desc.items():
    #value_list = list(set(value_list))  # 注释掉开启狂——暴——模式
    num = 1000  # 设置每个身份描述的样本数量
    # 如果描述少于num个，则生成两个描述列表
    if len(value_list) < num:
        value_list1 = value_list
        value_list2 = copy.deepcopy(value_list)
        random.shuffle(value_list2)  # 打乱第二个描述列表
    else:
        value_list1 = random.sample(value_list, num)  # 随机抽取num个描述
        value_list2 = random.sample(value_list, num)  # 随机抽取另一个num个描述
    print(key, count, len(identity_desc), len(value_list))  # 打印当前身份及其描述数量
    count += 1
    # 生成正样本对
    for s1, s2 in zip(value_list1, value_list2):  # 遍历两个描述列表
        if s1 == s2:  # 如果两个描述相同，则跳过
            continue
        print(key)  # 打印身份
        print(s1)  # 打印第一个描述
        print(s2)  # 打印第二个描述
        print("\n\n")
        # 构建正样本数据格式 [描述1, 描述2, 1]，表示这两个描述是相关的
        pos_data.append(str([s1, s2, 1]))

# 如果没有找到描述，则输出错误信息并退出
if not all_desc:
    print("No descriptions found in the input data. Exiting...")
else:
    # 生成负样本数据数量，通常是正样本的两倍
    neg_num = len(pos_data) * 2
    # 生成负样本描述，确保数量满足
    neg_desc = (neg_num // len(all_desc)) * all_desc + random.sample(all_desc, neg_num % len(all_desc))
    neg_desc2 = copy.deepcopy(neg_desc)

    random.shuffle(neg_desc2)  # 打乱负样本列表
    # 构建负样本数据格式 [描述1, 描述2, 0]，表示这两个描述不相关
    neg_data = [str([s1, s2, 0]) for s1, s2 in zip(neg_desc, neg_desc2)]

    # 将正负样本写入文件
    with open("train_data.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(pos_data + neg_data))  # 写入文件，格式化为每行一个样本

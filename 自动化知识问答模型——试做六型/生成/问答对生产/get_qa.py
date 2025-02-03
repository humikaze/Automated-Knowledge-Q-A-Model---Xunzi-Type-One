import datetime
import time
import requests
import uuid
from requests.exceptions import JSONDecodeError, Timeout


API_URL = "https://api.deepseek.com/v1/chat/completions"
API_KEY = 'sk-c65073ad363a493db1121bdddf1ef931'
MODEL_NAME = "deepseek-chat"
MAX_CONTENT_LENGTH = 2000  # 单次请求最大内容长度（字符数）#决定有多少内容


PROMPT_TEMPLATE_QUESTION = '''
#01 你是一个问答对数据集处理专家。

#02 你的任务是根据我给出的内容，生成适合作为问答对数据集的问题。

#03 问题要尽量短，不要太长。

#04 一句话中只能有一个问题。

#05 生成的问题必须宏观、价值，不要生成特别细节的问题。

#06 生成问题示例：

"""

权益型基金的特点有哪些方面？

介绍一下产品经理。

"""

#07 以下是我给出的内容：

"""

{{此处替换成你的内容}}

"""
'''

PROMPT_TEMPLATE_QA = '''
#01 你是一个问答对数据集处理专家。

#02 你的任务是根据我的问题和我给出的内容，生成对应的问答对。

#03 答案要全面，多使用我的信息，内容要更丰富。

#04 你必须根据我的问答对示例格式来生成：

"""

{"content": "基金分类有哪些", "summary": "根据不同标准，可以将证券投资基金划分为不同的种类：（1）根据基金单位是否可增加或赎回，可分为开放式基金和封闭式基金。开放式基金不上市交易（这要看情况），通过银行、券商、基金公司申购和赎回，基金规模不固定；封闭式基金有固定的存续期，一般在证券交易场所上市交易，投资者通过二级市场买卖基金单位。（2）根据组织形态的不同，可分为公司型基金和契约型基金。基金通过发行基金股份成立投资基金公司的形式设立，通常称为公司型基金；由基金管理人、基金托管人和投资人三方通过基金契约设立，通常称为契约型基金。我国的证券投资基金均为契约型基金。（3）根据投资风险与收益的不同，可分为成长型、收入型和平衡型基金。（4）根据投资对象的不同，可分为股票基金、债券基金、货币基金和混合型基金四大类。"}

{"content": "基金是什么", "summary": "基金，英文是fund，广义是指为了某种目的而设立的具有一定数量的资金。主要包括公积金、信托投资基金、保险基金、退休基金，各种基金会的基金。从会计角度透析，基金是一个狭义的概念，意指具有特定目的和用途的资金。我们提到的基金主要是指证券投资基金。"}

#05 我的问题如下：

"""

{{此处替换成你上一步生成的问题}}

"""

#06 我的内容如下：

"""

{{此处替换成你的内容}}

"""
'''


# ==================== 工具函数 ====================
'''
函数名: write_to_file
输入: content (str类型)
调用: 无外部调用
返回: 无
整体功能: 实现带重试机制的文件写入，自动生成带时间戳的唯一文件名
其他注释:

最多重试3次，每次间隔0.5秒

文件名格式为knowledge_年月日时分秒.txt

自动过滤空内容写入
'''
def write_to_file(content):
    """带重试的文件写入"""
    if not content:
        print("警告：尝试写入空内容")
        return

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    file_name = f"knowledge_{timestamp}.txt"

    for attempt in range(3):
        try:
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"成功写入文件：{file_name}")
            return
        except Exception as e:
            print(f"文件写入失败（尝试{attempt + 1}）: {str(e)}")
            time.sleep(0.5)
    print("文件写入最终失败")

'''
函数名: read_file
输入: file_path (str类型)
调用: 无外部调用
返回: str | None
整体功能: 实现带编码异常处理的文件读取
其他注释:

支持UTF-8和GBK双编码自动切换

最多重试3次读取

明确处理文件不存在异常
'''
def read_file(file_path):
    """带异常处理的文件读取"""
    for attempt in range(3):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            print(f"文件不存在：{file_path}")
            return None
        except UnicodeDecodeError:
            print(f"解码失败（尝试{attempt + 1}），尝试GBK编码...")
            try:
                with open(file_path, "r", encoding="gbk") as f:
                    return f.read()
            except:
                continue
        except Exception as e:
            print(f"读取失败（尝试{attempt + 1}）: {str(e)}")
            time.sleep(0.5)
    print("文件读取最终失败")
    return None

'''
函数名: chunk_content
输入: content (str类型), chunk_size (int类型，默认MAX_CONTENT_LENGTH)
调用: 无外部调用
返回: list[str]
整体功能: 智能分块长文本内容
其他注释:

按段落(\n分割)进行分块

保证每个分块不超过指定长度

自动过滤空段落并保持段落完整性
'''
def chunk_content(content, chunk_size=MAX_CONTENT_LENGTH):
    """智能分块文本内容"""
    paragraphs = content.split('\n')
    chunks = []
    current_chunk = []
    current_length = 0

    for p in paragraphs:
        p = p.strip()
        if not p:
            continue

        # 新增：处理超长段落
        if len(p) > chunk_size:
            if current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
                current_length = 0
            chunks.append(p[:chunk_size])
            continue

        if current_length + len(p) > chunk_size and current_chunk:
            chunks.append('\n'.join(current_chunk))
            current_chunk = []
            current_length = 0

        current_chunk.append(p)
        current_length += len(p)

    if current_chunk:
        chunks.append('\n'.join(current_chunk))

    print(f"已将内容分块为 {len(chunks)} 个段落")
    return chunks


'''
函数名: find_most_relevant_chunk
输入: question (str类型), content_chunks (list[str]类型)
调用: 无外部调用
返回: str
整体功能: 基于关键词匹配寻找最相关内容块
其他注释:

使用朴素的关键词交集算法

无匹配时返回第一个内容块

后续可升级为TF-IDF等算法
'''
def find_most_relevant_chunk(question, content_chunks):
    """寻找最相关的内容分块（简单实现）"""
    keywords = set(question.lower().split())
    best_score = 0
    best_chunk = ""

    for chunk in content_chunks:
        chunk_words = set(chunk.lower().split())
        score = len(keywords & chunk_words)
        if score > best_score:
            best_score = score
            best_chunk = chunk

    return best_chunk if best_score > 0 else content_chunks[0]
'''
函数名: check_network
输入: 无
调用: requests.post
返回: bool
整体功能: 执行网络连接和API认证检查
其他注释:

发送测试请求"ping"

识别401状态码(密钥无效)

包含完整错误类型诊断
'''

def check_network():
    """改进的网络诊断"""
    print("执行网络诊断...")
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }
        test_data = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 1
        }
        response = requests.post(
            API_URL,
            headers=headers,
            json=test_data,
            timeout=1000
        )

        if response.status_code == 200:
            print("✅ API服务可达且认证成功")
            return True
        elif response.status_code == 401:
            print("❌ 认证失败：无效的API密钥")
            return False
        else:
            print(f"⚠️ 服务响应异常 [{response.status_code}]：{response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ 连接失败：{str(e)}")
        return False

# ==================== API处理函数 ====================
'''
函数名: safe_api_call (装饰器)
输入: max_retries, initial_delay, backoff_factor
调用: 被装饰的函数
返回: wrapper函数
整体功能: 为API调用添加重试和异常处理逻辑
其他注释:

实现指数退避重试策略

处理HTTP错误/超时/JSON解析异常

验证响应数据结构完整性
'''


def safe_api_call(max_retries=3, initial_delay=1, backoff_factor=2):
    """改进的API调用装饰器，增强错误处理"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            current_delay = initial_delay
            for attempt in range(max_retries):
                try:
                    response = func(*args, **kwargs)

                    # 检查响应类型
                    if isinstance(response, str):
                        return response

                    # 打印响应状态和头信息以便调试
                    print(f"响应状态码: {response.status_code}")
                    print(f"响应头: {dict(response.headers)}")

                    # 检查响应内容
                    if not response.content:
                        print(f"[Attempt {attempt + 1}] 收到空响应")
                        continue

                    # 尝试解析前先检查响应内容
                    try:
                        response_text = response.text
                        print(f"响应内容前100字符: {response_text[:100]}")

                        if response.status_code != 200:
                            print(f"[Attempt {attempt + 1}] 请求失败，状态码：{response.status_code}")
                            print(f"错误响应: {response_text[:200]}")
                            continue

                        response_json = response.json()

                        if "choices" not in response_json:
                            print(f"[Attempt {attempt + 1}] 响应结构异常，缺少choices字段")
                            print(f"完整响应: {response_json}")
                            continue

                        choices = response_json["choices"]
                        if not isinstance(choices, list) or len(choices) == 0:
                            print(f"[Attempt {attempt + 1}] 无效的choices格式")
                            continue

                        message = choices[0].get("message", {})
                        content = message.get('content', '').strip()

                        if not content:
                            print(f"[Attempt {attempt + 1}] 空content字段")
                            continue

                        return content

                    except JSONDecodeError as je:
                        print(f"[Attempt {attempt + 1}] JSON解析失败")
                        print(f"错误位置: 行 {je.lineno}, 列 {je.colno}")
                        print(f"错误消息: {str(je)}")
                        print(f"响应内容: {response_text[:200]}")

                except Timeout as e:
                    print(f"[Attempt {attempt + 1}] 请求超时：{str(e)}")
                except Exception as e:
                    print(f"[Attempt {attempt + 1}] 未处理异常：{type(e).__name__} - {str(e)}")

                if attempt < max_retries - 1:
                    print(f"{current_delay}秒后重试...")
                    time.sleep(current_delay)
                    current_delay *= backoff_factor

            print(f"⚠️ 达到最大重试次数({max_retries})")
            return None

        return wrapper

    return decorator

'''
函数名: generate_question
输入: text_content (str类型), more (bool类型)
调用: requests.post
返回: str | None
整体功能: 调用API生成与内容相关的问题列表
其他注释:

自动截断超过450字符的内容

通过more参数控制生成问题数量(5/20)

请求头包含UUID追踪标识
'''
@safe_api_call(max_retries=5, initial_delay=2, backoff_factor=2)
def generate_question(text_content, more=False):
    """生成问题（自动分块处理）"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "X-Request-ID": str(uuid.uuid4()),
    }

    if len(text_content) > MAX_CONTENT_LENGTH * 5:  # 从3改为5
        print("⚠️ 警告：输入内容过长，执行智能摘要...")
        text_content = text_content[:MAX_CONTENT_LENGTH * 5] + "\n[已截断过长内容]"

    prompt = PROMPT_TEMPLATE_QUESTION.replace("{{此处替换成你的内容}}", text_content)

    response = requests.post(
        API_URL,
        headers=headers,
        json={
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": "生成60个高质量问题" if more else "生成40个核心问题"}
            ]
        },
        timeout=(10, 3000)
    )
    return response

'''
函数名: generate_qa
输入: text_content (str类型), question_text (str类型)
调用: requests.post
返回: str | None
整体功能: 生成结构化问答对数据
其他注释:

采用双阶段分块处理(问题块+内容块)

每个问答对限制最大5000字符

输出符合JSON Lines格式
'''


# 修改generate_qa函数为即时输出版本
@safe_api_call(max_retries=5, initial_delay=2, backoff_factor=2)
def generate_qa(text_content, question_text, chunk_index):
    """生成问答对（即时输出版本）"""
    if not question_text:
        print("❌ 错误：问题文本为空")
        return None

    q_chunks = chunk_content(question_text, chunk_size=8000)
    t_chunks = chunk_content(text_content)

    for q_idx, q_chunk in enumerate(q_chunks):
        best_chunk = find_most_relevant_chunk(q_chunk, t_chunks)
        if not best_chunk:
            continue

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "X-Request-ID": str(uuid.uuid4()),
        }

        prompt = PROMPT_TEMPLATE_QA.replace(
            "{{此处替换成你上一步生成的问题}}", q_chunk
        ).replace(
            "{{此处替换成你的内容}}", best_chunk
        )

        response = requests.post(
            API_URL,
            headers=headers,
            json={
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "生成JSON格式问答对"}
                ]
            },
            timeout=(10, 3000)
        )

        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"].strip()
            if content:
                # 立即写入文件，使用chunk_index和q_idx确保文件名唯一
                timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                file_name = f"knowledge_{timestamp}_chunk_{chunk_index}_q_{q_idx}.txt"
                try:
                    with open(file_name, "w", encoding="utf-8") as f:
                        f.write(content)
                    print(f"✍️ 已写入文件：{file_name}")
                except Exception as e:
                    print(f"❌ 文件写入失败: {str(e)}")

                # 返回内容以保持与原函数兼容
                return content

    return None


def merge_round_files(round_number):
    """合并单轮生成的所有问答文件

    Args:
        round_number: 轮次编号
    Returns:
        bool: 合并是否成功
    """
    import glob
    import os

    # 获取当前日期作为文件匹配模式
    current_date = datetime.datetime.now().strftime("%Y%m%d")

    # 查找该轮次生成的所有文件
    pattern = f"knowledge_{current_date}*.txt"
    files = glob.glob(pattern)

    if not files:
        print(f"⚠️ 第{round_number}轮没有找到可合并的文件")
        return False

    # 读取所有文件内容
    all_content = []
    try:
        for file in sorted(files):  # 排序确保按文件名顺序合并
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:  # 只添加非空内容
                    all_content.append(content)

            # 读取后删除单个文件
            os.remove(file)
            print(f"✓ 已处理并删除文件: {file}")
    except Exception as e:
        print(f"❌ 读取文件时出错: {str(e)}")
        return False

    if not all_content:
        print("⚠️ 没有有效的内容可合并")
        return False

    # 生成合并后的文件名
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    merged_filename = f"merged_knowledge_round_{round_number}_{timestamp}.txt"

    # 写入合并后的文件
    try:
        with open(merged_filename, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(all_content))
        print(f"✅ 第{round_number}轮文件合并完成: {merged_filename}")
        print(f"📊 合并了{len(files)}个文件，包含{len(all_content)}组问答对")
        return True
    except Exception as e:
        print(f"❌ 写入合并文件时出错: {str(e)}")
        return False


# ==================== 主流程 ====================
'''
函数名: main
输入: 无
调用: check_network, read_file, generate_question, generate_qa, write_to_file
返回: 无
整体功能: 核心执行流程控制器
其他注释:

包含完整的错误提前返回机制

执行内容分块并行处理

最终输出知识库文件
'''


def main():
    """改进的主流程（支持即时输出和轮次合并）"""
    if not check_network():
        print("请检查网络连接或API密钥有效性")
        return

    if (text_content := read_file("txt1.txt")) is None:
        return

    print(f"📖 已读取内容（{len(text_content)}字符）")

    chunks = chunk_content(text_content)
    chunk_counter = 0

    # 对每个块生成并处理问题
    for chunk_idx, chunk in enumerate(chunks):
        if questions := generate_question(chunk, more=True):
            print(f"✨ 第{chunk_idx + 1}块生成问题成功")

            # 直接处理这个块的问题
            q_chunks = chunk_content(questions, chunk_size=8000)
            for q_chunk in q_chunks:
                if qa_pairs := generate_qa(text_content, q_chunk, chunk_counter):
                    chunk_counter += 1
                    print(f"✅ 已处理第 {chunk_counter} 个问答块")


'''
执行控制块
输入: 无
调用: main
返回: 无
整体功能: 多轮执行和性能监控
其他注释:

循环执行5次完整流程

记录单次/总耗时

包含可视化进度提示(🚀/⏱️符号)
'''

if __name__ == "__main__":
    total_start = time.time()
    for i in range(1, 6):
        print(f"\n🚀 第 {i} 次执行开始")
        start_time = time.time()
        main()
        # 每轮结束后进行文件合并
        merge_round_files(i)
        print(f"⏱️ 本轮耗时：{time.time() - start_time:.2f}秒")

    print(f"\n✅ 全部执行完成，总耗时：{time.time() - total_start:.2f}秒")
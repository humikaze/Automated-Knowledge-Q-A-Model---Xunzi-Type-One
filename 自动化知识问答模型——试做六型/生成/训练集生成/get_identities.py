import json  # 导入json模块，用于处理JSON文件格式的数据
import jieba  # 导入jieba模块，用于中文分词
from sklearn.feature_extraction.text import TfidfVectorizer  # 导入TfidfVectorizer类，用于从文本中提取TF-IDF特征
from sklearn.metrics.pairwise import cosine_similarity  # 导入cosine_similarity函数，用于计算余弦相似度


def load_knowledge(file_path):
    """
    从指定路径加载JSON格式的知识数据。
    参数:
        file_path (str): 知识数据文件路径
    返回:
        data (list): 从文件中解析出来的所有JSON对象组成的列表
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        # 逐行读取文件并解析每行的JSON数据
        data = [json.loads(line) for line in f.readlines()]
    return data  # 返回加载的所有数据列表


def extract_keywords(data):
    """
    提取知识数据中的唯一关键词。
    参数:
        data (list): 知识数据，包含多个问题描述的JSON对象
    返回:
        unique_keywords (list): 从文本数据中提取出的唯一关键词列表
    """
    # 提取每个JSON对象中的'Q'字段，即问题描述
    questions = [item['Q'] for item in data]

    # 使用jieba分词库进行中文分词
    questions_tokenized = [' '.join(jieba.lcut(question)) for question in questions]

    # 读取停用词文件，并将停用词存储在集合中
    stop_words = set()
    with open('hit_stopwords.txt', 'r', encoding='utf-8') as f:
        stop_words.update([line.strip() for line in f])

    stop_words = list(stop_words)  # 将停用词集合转为列表

    # 使用TfidfVectorizer提取每个问题的TF-IDF特征
    vectorizer = TfidfVectorizer(
        token_pattern=r'(?u)\b\w+\b',  # 词的匹配模式
        stop_words=stop_words,  # 设置停用词
        max_features=400  # 设置最大特征数为400
    )
    tfidf_matrix = vectorizer.fit_transform(questions_tokenized)  # 计算所有问题的TF-IDF矩阵
    keywords = vectorizer.get_feature_names_out()  # 获取TF-IDF矩阵中的关键词

    # 计算关键词之间的余弦相似度
    similarities = cosine_similarity(tfidf_matrix.T)

    unique_keywords = []  # 存储唯一关键词的列表
    for idx, word in enumerate(keywords):  # 遍历每个关键词及其索引
        # 如果该词与其他词的相似度都小于0.8，则认为该词是唯一的
        if all(similarities[idx, j] < 0.8 for j in range(len(keywords)) if j != idx):
            unique_keywords.append(word)  # 将该词添加到唯一关键词列表中

    return unique_keywords  # 返回唯一关键词列表


def save_keywords(keywords, output_path):
    """
    将唯一关键词保存到指定的文件中。
    参数:
        keywords (list): 需要保存的关键词列表
        output_path (str): 输出文件的路径
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        # 遍历每个关键词并写入文件，每个关键词占一行
        for keyword in keywords:
            f.write(f"{keyword}\n")


input_file = 'knowledge.json'  # 输入文件路径
output_file = 'title_identities.txt'  # 输出文件路径

# 加载知识数据
data = load_knowledge(input_file)

# 提取唯一关键词
unique_keywords = extract_keywords(data)

# 将关键词保存到输出文件
save_keywords(unique_keywords, output_file)

# 打印提示信息
print(f"Unique keywords have been saved to {output_file}")

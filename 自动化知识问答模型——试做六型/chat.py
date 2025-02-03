import tkinter as tk
from tkinter import scrolledtext
from transformers import AutoTokenizer, AutoModel, BertTokenizer, BertModel, BertForSequenceClassification
import numpy as np
import pickle
import json
import torch
import os
from characterglm_generation_utils import SessionMeta
from inspect import signature
import sys
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

device = torch.device("cuda:0")
with open("id_vector", "rb") as f:
    faiss_index = pickle.load(f)
model_path = "my_model"
tokenizer = BertTokenizer.from_pretrained(model_path)
recall_model = BertModel.from_pretrained(model_path)
rank_model = BertForSequenceClassification.from_pretrained('rank_model')

chat_tokenizer = AutoTokenizer.from_pretrained("/tmp/pycharm_project_520/chatglm/chatglm2/model", trust_remote_code=True)
chat_model = AutoModel.from_pretrained("/tmp/pycharm_project_520/chatglm/chatglm2/model", trust_remote_code=True).cuda()
chat_model = chat_model.to(device)

rank_model = rank_model.to(device)
recall_model = recall_model.to(device)


def get_similar_query(query, num=3):
    results = []
    for _ in range(num):
        session_meta = SessionMeta(bot_name="Assistant", user_name="User")
        response, _ = chat_model.chat(
            chat_tokenizer,
            session_meta,
            query + "。改写上述话",
            history=[],
            do_sample=True,
            num_beams=3,
            temperature=2.0
        )
        results.append(response)
    return results


def read_knowledge(path):
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    data = [json.loads(line.strip()) for line in lines]
    id_desc = {}
    for s in data:
        id = s['id']
        id_desc[id] = s
    return id_desc


def normal(vector):
    vector = vector.tolist()[0]
    ss = sum([s ** 2 for s in vector]) ** 0.5
    return [s / ss for s in vector]


def get_vector(sentence):
    encoded_input = tokenizer([sentence], padding=True, truncation=True, max_length=512, return_tensors='pt')
    encoded_input = encoded_input.to(device)
    with torch.no_grad():
        model_output = recall_model(**encoded_input)
    sentence_embeddings = normal(model_output[1])
    sentence_embeddings = np.array([sentence_embeddings])
    return sentence_embeddings


def get_candidate(input, num=20):
    vector = get_vector(input)
    D, I = faiss_index.search(vector, num)
    D = D[0]
    I = I[0]
    indexs = []
    for d, i in zip(D, I):
        indexs.append(i)
    return indexs


def rank_sentence(query, sentences):
    X = [[query[0:200], sentence[0:200]] for sentence in sentences]
    X = tokenizer(X, padding=True, truncation=True, max_length=512, return_tensors='pt')
    X = X.to(device)
    scores = rank_model(**X).logits
    scores = torch.softmax(scores, dim=-1).tolist()
    # 打分为0-1判别相似度
    scores = [round(s[1], 3) for s in scores]
    return scores


def rag_recall(query):
    similar_queries = get_similar_query(query)
    index_score = {}
    for input in [query] + similar_queries:
        indexs = get_candidate(input, num=30)
        sentences = [id_knowledge[index]['Q'] for index in indexs]
        scores = rank_sentence(input, sentences)
        for index, score in zip(indexs, scores):
            if score < 0.9:
                continue
            index_score[index] = index_score.get(index, 0.0) + score

    results = sorted(index_score.items(), key=lambda s: s[1], reverse=True)
    return results[0:3]

def get_prompt(recall_result):
    prompt = ""
    for i, [recall_id, recall_score] in enumerate(recall_result):
        prompt += f"实例{i}: 提问：{id_knowledge[recall_id]['Q']} 回答:{id_knowledge[recall_id]['A']}。"
    return prompt

id_knowledge = read_knowledge("knowledge.json")
while True:
    session_meta = SessionMeta(
        bot_name="Assistant",  # 设置机器人名称
        user_name="User",  # 设置用户名称

    )
    sys.stdout = sys.__stdout__  # 恢复输出
    query = input("输入问题: ")
    sys.stdout = open(os.devnull, 'w')
    recall_result = rag_recall(query)
    prompt = get_prompt(recall_result)
    # 经验
    response, _ = chat_model.chat(chat_tokenizer,
                                  session_meta,
                                  prompt + "根据上述实例，给出下述问题的答案" + query,
                                  history=[],
                                  num_beams=3
                                  )
    sys.stdout = sys.__stdout__  # 恢复输出
    print(response)
    sys.stdout = open(os.devnull, 'w')
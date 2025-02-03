import json
from transformers import BertTokenizer, BertModel
import torch
import faiss
import numpy as np
import pickle
device = torch.device("cuda:0")
model_path = "my_model"
tokenizer = BertTokenizer.from_pretrained(model_path)
model = BertModel.from_pretrained(model_path).cuda()
def get_vector(sentence):
    encoded_input = tokenizer([sentence], padding = True, truncation = True, max_length = 512, return_tensors = 'pt')
    encoded_input = encoded_input.to(device)
    with torch.no_grad():
        model_output = model(**encoded_input)
    sentence_embeddings = model_output[1]
    return sentence_embeddings

def normal(vector):
    vector = vector.tolist()[0]
    ss = sum([s**2 for s in vector]) ** 0.5
    return [round(s/ss, 5) for s in vector]
with open("knowledge.json", encoding = "utf-8") as f:
    lines = f.readlines()
    identity_desc = {}
    all_desc = []
    data = [json.loads(line.strip()) for line in lines]
    id_vector = []
    count = 0
    for s in data:
        count += 1
        print(count, len(data))
        desc = s["Q"]
        id = s['id']
        vector = get_vector(desc)
        vector = normal(vector)
        id_vector.append(vector)
    index = faiss.IndexFlatL2(768)
    id_vector = np.array(id_vector)
    index.add(id_vector)
    with open("id_vector", "wb") as f:
        pickle.dump(index, f)

from transformers import BertTokenizer, BertModel
import torch
from torch import nn
from torch.utils.data import DataLoader
from torch.utils.data import Dataset
import torch.optim as optim
import torch.nn.functional as F
import random
import numpy as np
import os

class DSSM(nn.Module):
    def __init__(self, bert_model, t):
        super(DSSM, self).__init__()
        self.bert_model = bert_model
        #温度系数t
        self.t = t
    def forward(self, x1, x2):
        v1 = self.bert_model(**x1)
        v2 = self.bert_model(**x2)
        similar = torch.cosine_similarity(v1[1], v2[1], dim=1)
        #归一化
        y = nn.Sigmoid()(similar / self.t)
        return y

device = torch.device("cuda:0")
tokenizer = BertTokenizer.from_pretrained('model')
model = BertModel.from_pretrained('model')
#双塔模型
dssm = DSSM(model, 0.05)
dssm = dssm.to(device)
with open("train_data.txt", encoding="utf-8") as f:
    lines = [eval(s.strip()) for s in f.readlines()]
#print (model)
#只训练最后一层
for name, s in model.named_parameters():
    if "pooler.dense" in name:
        s.requires_grad = True
    else:
        s.requires_grad = False
optimizer = optim.Adam(dssm.parameters(), lr=0.001)

batch_size = 96 * 8
dssm.train()
for epoch in range(0, 1000):
    num = len(lines) // batch_size
    random.shuffle(lines)
    for step in range(0, num):
        print(epoch, step, num)
        sub_lines = lines[step * batch_size:(step + 1) * batch_size]
        X1, X2, Y = zip(*sub_lines)
        X1 = list(X1)
        X2 = list(X2)

        X1 = tokenizer(X1, padding=True, truncation=True, max_length=512, return_tensors='pt')
        X2 = tokenizer(X2, padding=True, truncation=True, max_length=512, return_tensors='pt')
        Y = torch.tensor(Y, dtype=float)
        X1, X2, Y = X1.to(device), X2.to(device), Y.to(device)
        output = dssm(X1, X2)
        loss = nn.BCELoss()(output.view(-1, 1), Y.float().view(-1, 1))
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
        if step % 10 == 0:
            print(loss)
            #只保存Bert
            torch.save(model.state_dict(), os.path.join("my_model", "pytorch_model.bin"))

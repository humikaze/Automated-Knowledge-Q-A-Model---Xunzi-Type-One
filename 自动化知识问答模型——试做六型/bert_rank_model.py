from transformers import BertTokenizer, BertForSequenceClassification
import torch
from torch import nn
from torch.utils.data import DataLoader
from torch.utils.data import Dataset
import torch.optim as optim
import torch.nn.functional as F
import random
import numpy as np
import os

device = torch.device("cuda:0")
tokenizer = BertTokenizer.from_pretrained('model')

model = BertForSequenceClassification.from_pretrained('model')
model = model.to(device)
with open("train_data.txt", encoding="utf-8") as f:
    lines = [eval(s.strip()) for s in f.readlines()]

for name, s in model.named_parameters():
    if "encoder.layer.11" in name or "pooler.dense" in name or "classifier" in name:
        s.requires_grad = True
    else:
        s.requires_grad = False

def convert_Y(y):
    s = [0, 0]
    s[y] = 1
    return s

optimizer = optim.Adam(model.parameters(), lr=0.001)
batch_size = 96 * 8
model.train()
for epoch in range(0, 100):
    num = len(lines) // batch_size
    random.shuffle(lines)
    for step in range(0, num):
        print(epoch, step, num)
        sub_lines = lines[step * batch_size:(step + 1) * batch_size]
        X1, X2, Y = zip(*sub_lines)
        X1 = list(X1)
        X2 = list(X2)
        #每个句子截取200个字符以尽量接近bert上限
        X = [[s1[0:200], s2[0:200]] for s1, s2 in zip(X1, X2)]
        Y = [convert_Y(s) for s in Y]
        X = tokenizer(X, padding=True, truncation=True, max_length=512, return_tensors='pt')
        Y = torch.tensor(Y, dtype=float)
        X, Y = X.to(device), Y.to(device)
        output = model(**X).logits
        loss = nn.BCEWithLogitsLoss()(output, Y)
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
        if step % 10 == 0:
            print(loss)
            torch.save(model.state_dict(), os.path.join("rank_model", "pytorch_model.bin"))


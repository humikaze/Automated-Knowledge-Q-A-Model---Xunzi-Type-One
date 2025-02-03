from flask import Flask, request, jsonify, render_template_string
import torch
from transformers import AutoTokenizer, AutoModel, BertTokenizer, BertModel, BertForSequenceClassification
import numpy as np
import pickle
import json
import os
from characterglm_generation_utils import SessionMeta
import sys
#import faiss

app = Flask(__name__)

# HTML 页面直接嵌入到 Python 代码中
html_content = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>自动化知识问答模型——巽伊</title>
    <style>
        /* 动态渐变背景 */
        @keyframes cosmicFlow {
            0% {
                background-position: 0% 50%;
                background-size: 200% 200%;
            }
            50% {
                background-position: 100% 50%;
                background-size: 180% 180%;
            }
            100% {
                background-position: 0% 50%;
                background-size: 200% 200%;
            }
        }

        body {
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(
                135deg,
                #667eea 0%,
                #764ba2 25%,
                #a3bded 50%,
                #f6d5f7 75%,
                #667eea 100%
            );
            background-size: 200% 200%;
            animation: cosmicFlow 18s ease infinite;
            padding: 20px;
        }

        /* 聊天容器 */
        .chat-box {
            width: 100%;
            max-width: 800px;
            height: 80vh;
            background: rgba(255, 255, 255, 0.88);
            backdrop-filter: blur(12px);
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.3);
        }

        /* 消息区域 */
        #messages {
            flex: 1;
            padding: 24px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
 
        /* 消息气泡 */
        .message {
            max-width: 75%;
            padding: 16px 20px;
            border-radius: 20px;
            line-height: 1.5;
            font-size: 16px;
            transition: transform 0.2s ease-out;
            position: relative;
            word-break: break-word;
        }
        
        .user-message {
            background: #4f46e5;
            color: white;
            align-self: flex-end;
            border-radius: 20px 20px 4px 20px;
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2);
        }


        .assistant-message {
            background: rgba(255, 255, 255, 0.95);
            color: #1f2937;
            align-self: flex-start;
            border-radius: 20px 20px 20px 4px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        }

        /* 输入区域 */
        .input-area {
            padding: 20px;
            background: rgba(255, 255, 255, 0.9);
            border-top: 1px solid rgba(0, 0, 0, 0.05);
            display: flex;
            gap: 12px;
        }


        .input-area textarea {
            flex: 1;
            padding: 14px 20px;
            border: none;
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.95);
            box-shadow: 
                inset 0 2px 4px rgba(0, 0, 0, 0.05),
                0 2px 8px rgba(0, 0, 0, 0.05);
            font-size: 16px;
            resize: none;
            transition: all 0.2s ease;
        }

        .input-area textarea:focus {
            outline: none;
            box-shadow: 
                inset 0 2px 8px rgba(0, 0, 0, 0.08),
                0 4px 16px rgba(79, 70, 229, 0.15);
        }

        .input-area button {
            padding: 12px 24px;
            border: none;
            border-radius: 16px;
            background: linear-gradient(135deg, #4f46e5, #6366f1);
            color: white;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .input-area button:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 16px rgba(79, 70, 229, 0.4);
        }

        .loading {
            font-size: 18px;
            color: #007bff;
            text-align: center;
            display: none;
        }

        .loading span {
            font-weight: bold;
        }

        .typing-indicator {
            font-size: 18px;
            color: #007bff;
            font-weight: bold;
            display: none;
            animation: typing 1.5s infinite;
        }

        @keyframes typing {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-4px); }
        }

        /* 响应式设计 */
        @media (max-width: 640px) {
            .chat-box {
                height: 90vh;
                border-radius: 16px;
            }

            .message {
                max-width: 85%;
                padding: 12px 16px;
            }

            button {
                padding: 12px 16px;
            }
        }
    </style>
</head>
<body>

<div class="chat-box" id="chatBox">
    <div id="messages">
        <!-- 聊天消息显示区域 -->
    </div>
    <div class="typing-indicator" id="typingIndicator">
        <span>天宇正在打字...</span>
    </div>


    <div class="input-area">
            <textarea id="userInput" placeholder="输入您的问题..." rows="1"></textarea>
            <button onclick="sendMessage()">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="22" y1="2" x2="11" y2="13"></line>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                </svg>
            </button>
     </div>
</div>

<script>
    // 显示用户消息
    function addMessage(message, type) {
        const messagesDiv = document.getElementById("messages");
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message");

        if (type === "user") {
            messageDiv.classList.add("user-message");
        } else if (type === "assistant") {
            messageDiv.classList.add("assistant-message");
        }

        messageDiv.textContent = message;
        messagesDiv.appendChild(messageDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    // 发送消息函数
    function sendMessage() {
        const userMessage = document.getElementById("userInput").value;
        if (userMessage.trim() === "") return;

        // 显示用户输入的消息
        addMessage(userMessage, "user");

        // 清空输入框
        document.getElementById("userInput").value = "";

        // 显示加载中动画
        const typingIndicator = document.getElementById("typingIndicator");
        typingIndicator.style.display = "block";

        // 发送POST请求到后端
        fetch('/send_message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ user_message: userMessage })
        })
        .then(response => response.json())
        .then(data => {
            // 隐藏加载中动画
            typingIndicator.style.display = "none";

            // 显示助手的回答
            displayAssistantResponse(data.model_response);
        })
        .catch(error => {
            console.error("Error:", error);
            typingIndicator.style.display = "none";  // 隐藏加载动画
        });
    }

    // 显示助手的逐字输出
    function displayAssistantResponse(responseText) {
        let index = 0;
        const assistantMessageDiv = document.createElement("div");
        assistantMessageDiv.classList.add("message", "assistant-message");
        document.getElementById("messages").appendChild(assistantMessageDiv);
        assistantMessageDiv.textContent = "";  // 清空助手消息

        const typingInterval = setInterval(() => {
            if (index < responseText.length) {
                assistantMessageDiv.textContent += responseText.charAt(index);
                index++;
            } else {
                clearInterval(typingInterval);  // 停止逐字显示
            }
        }, 50);  // 每50ms显示一个字符
    }
</script>

</body>
</html>
'''

# 机器学习模型及相关配置
device = torch.device("cuda:0")
with open("id_vector", "rb") as f:
    faiss_index = pickle.load(f)

model_path = "my_model"
tokenizer = BertTokenizer.from_pretrained(model_path)
recall_model = BertModel.from_pretrained(model_path)
rank_model = BertForSequenceClassification.from_pretrained('rank_model')

chat_tokenizer = AutoTokenizer.from_pretrained("/tmp/pycharm_project_520/chatglm/chatglm2/model",
                                               trust_remote_code=True)
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
@app.route('/')
def index():
    return render_template_string(html_content)

@app.route('/send_message', methods=['POST'])
def send_message():
    user_message = request.json.get("user_message")
    recall_result = rag_recall(user_message)
    prompt = get_prompt(recall_result)

    session_meta = SessionMeta(bot_name="Assistant", user_name="User")
    response, _ = chat_model.chat(
        chat_tokenizer,
        session_meta,
        prompt + "要求根据上述实例内容，给出下述问题的答案" + user_message,
        history=[],
        num_beams=10
    )

    return jsonify({'model_response': response})


# 处理favicon.ico请求，避免404
@app.route('/favicon.ico')
def favicon():
    return '', 204  # 返回204无内容状态码


if __name__ == '__main__':
    app.run(debug=True)

import requests
import json
from dotenv import load_dotenv
import os
import gradio as gr
import time
import base64  # 导入 base64 库，用于进行 Base64 编码
import re  # 导入正则表达式库，用于去除引用标记

load_dotenv()
APP_ID = os.getenv("APP_ID")
AUTHORIZATION_TOKEN = os.getenv("AUTHORIZATION_TOKEN")

conversation_id = None

def create_new_conversation():
    global conversation_id  # 声明使用全局变量 conversation_id
    url = "https://qianfan.baidubce.com/v2/app/conversation"  # API 的 URL

    # 构建请求的 payload
    payload = json.dumps({
        "app_id": APP_ID  # 使用应用的 APP_ID
    })
    # 设置请求头
    headers = {
        'Content-Type': 'application/json',  # 数据类型为 JSON
        'X-Appbuilder-Authorization': f'Bearer {AUTHORIZATION_TOKEN}'  # 使用 AUTHORIZATION_TOKEN 进行身份验证
    }

    # 发送 POST 请求以创建新会话
    response = requests.request("POST", url, headers=headers, data=payload)
    response_data = response.json()  # 将响应转换为 JSON 格式

    # 从响应数据中获取会话 ID
    conversation_id = response_data.get("conversation_id", None) 
    return conversation_id

def remove_references(text):
    # 匹配以 ^ 开头并以 ^ 结尾的内容，中间可能包含一个或多个 [n] 形式的引用
    text = re.sub(r'\^\[\d+\](\[\d+\])*\^', '', text)
    return text

def get_bot_response(user_input):
    global conversation_id
    url = "https://qianfan.baidubce.com/v2/app/conversation/runs"
    
    payload = json.dumps({
        "app_id": APP_ID,
        "query": user_input,
        "stream": True,
        "conversation_id": conversation_id
    })
    headers = {
        'Content-Type': 'application/json',
        'X-Appbuilder-Authorization': f'Bearer {AUTHORIZATION_TOKEN}'
    }
    
    response = requests.request("POST", url, headers=headers, data=payload, stream=True)
    
    bot_response = ""
    # 逐行读取响应并提取`answer`内容
    for line in response.iter_lines():
        if line:
            try:
                # 去掉前缀"data: "并解析JSON
                json_data = json.loads(line.decode('utf-8')[6:])
                answer = json_data.get("answer", "")
                
                # 使用正则表达式去除各种引用标记
                answer = remove_references(answer)
                
                bot_response += answer
                yield answer
            except json.JSONDecodeError:
                continue

def main():
    global conversation_id
    conversation_id = create_new_conversation()

# 将 logo.png 文件编码为 Base64
with open("logomin2.gif", "rb") as image_file:
    encoded_string = base64.b64encode(image_file.read()).decode()

# 定义开场白
opening_message = """你好，我是上海工程技术大学的虚拟辅导员“程智”，随时为你解答学校信息、新生入学、思想教育、教学管理、评奖评优、学生资助和事务服务等问题。

"""

with gr.Blocks() as demo:
    # 设置界面的标题和 logo
    gr.Markdown(
        f"""
        <h1 style='display: flex; align-items: center; justify-content: center;'>
            <img src='data:image/gif;base64,{encoded_string}' style='width: 50px; margin-right: 10px;' />
            <center>虚拟辅导员“程智”</center>
        </h1>
        """
    )
    # 初始化聊天历史记录
    chatbot = gr.Chatbot(value=[(None, opening_message)], min_width=120, show_label=False)
    msg = gr.Textbox(scale=1, placeholder="请输入您的问题....", show_label=False)
    with gr.Row():
        submit = gr.Button(value="🚀 发送", scale=1)
        clear = gr.Button(value="🧹 清屏", scale=1)
    # 添加页面底部的提示信息
    gr.HTML(
        f"""
        <div style='display: flex; align-items: center; justify-content: center; font-size: 8px; color: #CCCCCC;'>
            <center>如果您的问题尚未得到有效解决，请关注“程园学工”公众号私信留言</center>
        </div>
        """
    )
    def user(user_message, history):
        return "", history + [[user_message, None]]

    def bot(history):
        user_message = history[-1][0]  # 获取用户的最新消息
        bot_response_generator = get_bot_response(user_message)  # 使用生成器获取 bot 响应

        history[-1][1] = ""
        for bot_message in bot_response_generator:
            for character in bot_message:
                history[-1][1] += character
                time.sleep(0.05)
                yield history

    msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False).then(
        bot, chatbot, chatbot
    )
    submit.click(lambda x: x, inputs=[msg], outputs=[msg], queue=False).then(
        user, [msg, chatbot], [msg, chatbot], queue=False).then(bot, chatbot, chatbot)
    clear.click(lambda: None, None, chatbot, queue=False)

main()
demo.queue()
demo.launch(share=False)

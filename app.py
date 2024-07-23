import gradio as gr
import requests
import json
from dotenv import load_dotenv
import os

# 加载 .env 文件中的环境变量
load_dotenv()

# 从环境变量中获取敏感信息
APP_ID = os.getenv("APP_ID")
AUTHORIZATION_TOKEN = os.getenv("AUTHORIZATION_TOKEN")

# 定义全局变量来存储会话 ID
conversation_id = None

# 定义一个函数来创建新会话
def create_new_conversation():
    global conversation_id
    url = "https://qianfan.baidubce.com/v2/app/conversation"

    payload = json.dumps({
        "app_id": APP_ID
    })
    headers = {
        'Content-Type': 'application/json',
        'X-Appbuilder-Authorization': f'Bearer {AUTHORIZATION_TOKEN}'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    response_data = response.json()

    # 假设响应中有一个键 "conversation_id" 包含会话 ID
    conversation_id = response_data.get("conversation_id", None)

# 定义一个函数来处理对话
def chatbot(query, history):
    global conversation_id
    if conversation_id is None:
        create_new_conversation()

    url = "https://qianfan.baidubce.com/v2/app/conversation/runs"

    payload = json.dumps({
        "app_id": APP_ID,
        "query": query,
        "stream": False,
        "conversation_id": conversation_id
    })
    headers = {
        'Content-Type': 'application/json',
        'X-Appbuilder-Authorization': f'Bearer {AUTHORIZATION_TOKEN}'
    }

    response = requests.post(url, headers=headers, data=payload)
    response_data = response.json()

    # 假设响应中有一个键 "answer" 包含对话的回答
    answer = response_data.get("answer", "对不起，我没有理解你的问题。")

    # 更新聊天历史
    history.append((query, answer))

    return history, history, ""

# 创建 Gradio 界面
def create_interface():
    create_new_conversation()  # 每次创建界面时创建新会话

    with gr.Blocks() as iface:
        gr.Markdown("<h1><center>程园虚拟辅导员</center></h1>")
        chatbot_ui = gr.Chatbot()
        with gr.Row():
            with gr.Column(scale=8):
                txt = gr.Textbox(show_label=False, placeholder="请输入你的问题...")
            with gr.Column(scale=1):
                btn = gr.Button("发送")

        def scroll_to_bottom():
            js_code = """
            <script>
                const container = document.querySelector('.overflow-y-auto');
                if (container) {
                    container.scrollTop = container.scrollHeight;
                }
            </script>
            """
            return gr.HTML(js_code)

        btn.click(chatbot, [txt, chatbot_ui], [chatbot_ui, chatbot_ui, txt]).then(scroll_to_bottom, None)
        txt.submit(chatbot, [txt, chatbot_ui], [chatbot_ui, chatbot_ui, txt]).then(scroll_to_bottom, None)

    return iface

# 启动 Gradio 界面
if __name__ == "__main__":
    iface = create_interface()
    iface.launch(
        inbrowser=True,
        share=True,
        debug=True,
        server_name="0.0.0.0",
        server_port=7860
    )

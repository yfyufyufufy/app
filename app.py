from flask import Flask, request, abort
from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    PushMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    FollowEvent,
    TextMessageContent,
)
import utilities
from health_data_manager import HealthDataManager
from chatgpt import ChatGPT

app = Flask(__name__)
line_credential = utilities.read_config('./configs/line-api-credential.json') # 讀取LINE API 的訊息
configuration = Configuration(access_token = line_credential['accessToken']) # 配置 Line API 的訪問憑據
handler = WebhookHandler(line_credential['channelSecret'])  # 使用 channelSecret 創建 Webhook 處理器
health_manager = HealthDataManager("./configs./health-data-config.json") # 創建健康數據管理器實例
chatgpt = ChatGPT("./configs/chatgpt-credential.json") # 創建 ChatGPT 對話模型實例

# 127.0.0.1:9002/health-data?uid=abcdefg&hb=120&bo=98&bt=37.5
@app.route("/health-data", methods=["GET"])
def handle_health_data():
    vital_signs = health_manager.get_vital_signs(request.args) # 獲取健康數據
    health_judge = health_manager.get_health_judge(vital_signs) # 根據健康數據判斷健康狀況
    if health_judge:
        user_id = vital_signs[0]
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.push_message( # 向用戶發送健康提示消息
                PushMessageRequest(
                    to=user_id,
                    messages=[TextMessage(text=health_judge)]
                )
            )
    return 'OK'

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.") # 驗證用戶身分
        abort(400)

    return 'OK'
  
# 处理用户发送的文本消息
@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        user_id = event.source.user_id
        message = event.message.text
        reply_message = ""

        if message == "心跳":
            reply_message = f"最後一次測量心跳"
        elif message == "血氧":
            reply_message = f"最後一次測量血氧"
        elif message == "體溫":
            reply_message = f"最後一次測量體溫"
        else:
            reply_message = chatgpt.chat(message) # 使用 ChatGPT 進行對話

        line_bot_api.reply_message_with_http_info( # 回覆用戶發送的消息
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_message)]
            )
        )

@handler.add(FollowEvent)
def handle_follow(event):
    print("handling follow event")

if __name__ == "__main__":
    app.run(port=9002)

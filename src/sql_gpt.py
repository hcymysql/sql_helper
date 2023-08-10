# 付费玩家 - SQL改写（必须购买openai的账号才可以调用api，国内用户可以走代理访问。）
# 由于诸多限制，该功能无法合并到主分之版本里，留一个接口，以待来年。
import requests

class GptChatBot:
    def __init__(self, api_key):
        self.api_key = api_key
        self.api_url = 'https://api.openai-proxy.com/v1/chat/completions'
        self.model = 'gpt-3.5-turbo'
        self.temperature = 0.5

    def get_response(self, system_prompt, user_prompt):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        payload = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            'temperature': self.temperature
        }
        response = requests.post(self.api_url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return None

# 示例用法
api_key = "输入你的key(sk-......)"
bot = GptChatBot(api_key)
system_prompt = "SQL优化"
user_prompt = "请帮我优化：select * from t1 where id in (select id from t2) and name='aa'"
response = bot.get_response(system_prompt, user_prompt)
print(response)


# https://platform.deepseek.com/api_keys 申请密钥并充值1元

from openai import OpenAI
import re

def optimize_sql(original_sql):
    """
    调用 deepseek V3 接口优化 SQL 查询语句，并返回优化后的纯 SQL 字符串。

    Args:
        original_sql (str): 原始的 SQL 查询语句。

    Returns:
        str: 优化后的纯 SQL 查询语句。如果调用过程中发生错误，则返回包含错误信息的字符串。
    """
    try:
        client = OpenAI(api_key="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", base_url="https://api.deepseek.com")

        # 输出调用信息 (可选，仅用于调试)
        print('\033[94m以下是调用的deepseek V3接口.\033[0m')
        print('优化前的SQL是：')
        print(original_sql)
        print('-' * 55)

        # 获取优化后的 SQL，不要求返回 HTML 格式
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是MySQL专家！你精通SQL优化！也是高级程序员！"},
                {"role": "user", "content": f"帮我优化这个SQL，返回纯 SQL 语句，不要添加任何标记或格式：{original_sql}"},
            ],
            stream=False
        )
        
        # 获取优化后的 SQL 内容
        optimized_sql = response.choices[0].message.content
        
        # 清理可能的标记（例如 ```sql 或 ```），确保返回纯 SQL
        optimized_sql = re.sub(r'```sql|```|<\w+>.*?</\w+>', '', optimized_sql, flags=re.MULTILINE).strip()

        # 输出优化后的 SQL (可选，仅用于调试)
        print('\033[92m优化后的SQL是：\033[0m')
        print(optimized_sql)

        return optimized_sql

    except Exception as e:
        # 捕获异常，返回纯文本错误信息
        error_message = f"调用 deepseek API 接口出错: {str(e)}"
        print(error_message)  # 打印错误信息到控制台 (可选)
        return error_message

from vanna.remote import VannaDefault

def optimize_sql(original_sql):
    """
    调用 vanna.ai LLM 接口优化 SQL 查询语句，并返回优化后的 SQL 字符串。

    Args:
        original_sql (str): 原始的 SQL 查询语句。

    Returns:
        str: 优化后的 SQL 查询语句。 如果调用过程中发生错误，则返回包含错误信息的字符串。
    """
    try:
        # 创建 VannaDefault 实例
        vn = VannaDefault(model='sql_helper', api_key='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')

        # 输出调用信息 (可选，仅用于调试)
        print('\033[94m以下是调用的vanna.ai LLM接口.\033[0m')
        print('优化前的SQL是：')
        print(original_sql)
        print('-' * 55)

        # 获取优化后的 SQL
        #vn.ask('How to optimize this SQL : {}'.format(original_sql))
        optimized_sql = vn.generate_sql('How to optimize this SQL : {}'.format(original_sql))
 
        # 输出优化后的 SQL (可选，仅用于调试)
        print('\033[92m优化后的SQL是：\033[0m')

        return optimized_sql

    except Exception as e:
        # 捕获异常，返回包含错误信息的字符串
        error_message = f"调用 vanna.ai 优化出错: {e}"
        print(error_message)  # 打印错误信息到控制台 (可选)
        return error_message

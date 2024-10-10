from vanna.remote import VannaDefault

def optimize_sql(original_sql):
    # 创建 VannaDefault 实例
    vn = VannaDefault(model='sql_helper', api_key='xxxxxxxxxxxxxxxxxxxx')

    # 输出调用信息
    print('以下是调用的vanna.ai LLM接口.')
    print('优化前的SQL是：')
    print(original_sql)
    print('-' * 55)

    # 输出优化后的 SQL
    print('优化后的SQL是：')

    # 调用 VannaDefault 的 ask 方法
    vn.ask('How to optimize this SQL : {}'.format(original_sql))

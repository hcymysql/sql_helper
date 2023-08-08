import sys,re
import textwrap
from tabulate import tabulate
import pymysql
from sql_metadata import Parser
from sql_format_class import SQLFormatter
from sql_alias import has_table_alias
from sql_count_value import count_column_value
from sql_index import execute_index_query
import yaml
import argparse


# 创建命令行参数解析器
parser = argparse.ArgumentParser()
# 添加-f/--file参数，用于指定db.yaml文件的路径
parser.add_argument("-f", "--file", required=True, help="Path to db.yaml file")
# 添加--sql参数
parser.add_argument("-q","--sql", required=True, help="SQL query")
# 添加--sample参数，默认值为100000，表示10万行
parser.add_argument("--sample", default=100000, type=int, help="Number of rows to sample (default: 100000)")

# 解析命令行参数
args = parser.parse_args()

# 获取传入的db.yaml文件路径
file_path = args.file
# 获取样本数据行数
sample_size = args.sample

# 从外部的db.yaml文件加载配置
with open(file_path, "r") as f:
    db_config = yaml.safe_load(f)

# 使用加载的配置赋值给mysql_settings
mysql_settings = {
    "host": db_config["host"],
    "port": db_config["port"],
    "user": db_config["user"],
    "passwd": db_config["passwd"],
    "database": db_config["database"],
    "cursorclass": pymysql.cursors.DictCursor
}

# 获取传入的sql_query的值
sql_query = args.sql

print("你刚才输入的SQL语句是：")
print("-" * 100)
# 美化SQL
formatter = SQLFormatter()
formatted_sql = formatter.format_sql(sql_query)
print(formatted_sql)
print("-" * 100)

###########################################################################
# 解析SQL，识别出表名和字段名
try:
    parser = Parser(sql_query)
    table_names = parser.tables
    table_aliases = parser.tables_aliases
    data = parser.columns_dict
    select_fields = data.get('select', [])
    join_fields = data.get('join', [])
    where_fields = data.get('where', [])
    order_by_fields = data.get('order_by', [])
    group_by_fields = data.get('group_by', [])
    if 'SELECT' not in sql_query.upper():
        print("sql_helper工具仅支持select语句")
        sys.exit(1)
except Exception as e:
    print("解析 SQL 出现语法错误：", str(e))
    sys.exit(2)

###########################################################################
conn = pymysql.connect(**mysql_settings)
cur = conn.cursor()

sql = f"EXPLAIN {sql_query}"

try:
    cur.execute(sql)
except pymysql.err.ProgrammingError as e:
    print("MySQL 内部错误：",e)
    sys.exit(1)
except Exception as e:
    print("MySQL 内部错误：",e)
    sys.exit(1)
explain_result = cur.fetchall()

# 提取列名
e_column_names = list(explain_result[0].keys())

# 提取结果值并进行自动换行处理
e_result_values = []
for row in explain_result:
    values = list(row.values())
    wrapped_values = [textwrap.fill(str(value), width=20) for value in values]
    e_result_values.append(wrapped_values)

# 将结果格式化为表格（包含竖线）
e_table = tabulate(e_result_values, headers=e_column_names, tablefmt="grid", numalign="left")

print()
print("EXPLAIN执行计划:")
print(e_table)
print()
###########################################################################

# 判断有无where条件
if len(where_fields) == 0:
    print(f"你的SQL没有where条件.")

# 判断如果SQL里包含on，检查on后面的字段是否有索引。
if len(join_fields) != 0:
    table_field_dict = {}

    for field in join_fields:
        table_field = field.split('.')
        if len(table_field) == 2:
            table_name = table_field[0]
            field_name = table_field[1]
            if table_name not in table_field_dict:
                table_field_dict[table_name] = []
            table_field_dict[table_name].append(field_name)

    for table_name, on_columns in table_field_dict.items():
        for on_column in on_columns:
            show_index_sql = f"show index from {table_name} where Column_name = '{on_column}'"
            cur.execute(show_index_sql)
            index_result = cur.fetchall()
            if not index_result:
                print("join联表查询，on关联字段必须增加索引！")
                print(f"\033[91m需要添加索引：ALTER TABLE {table_name} ADD INDEX idx_{on_column}({on_column});\033[0m\n")
                print(f"【{table_name}】表 【{on_column}】字段，索引分析：")
                index_static = execute_index_query(mysql_settings, database=mysql_settings["database"], table_name=table_name, index_columns=on_column)
                print(index_static)

# 解析执行计划，查找需要加索引的字段
for row in explain_result:
    # 获取查询语句涉及的表和字段信息
    table_name = row['table']
    add_index_fields = []
    # 判断是否需要加索引的条件
    if (row['type'] == 'ALL' and row['key'] is None) or row['rows'] >= 1000:
        # 判断表是否有别名，没有别名的情况：
        if has_table_alias(table_aliases) is False:
            if len(where_fields) != 0:
                contains_dot = any('.' in field for field in where_fields)
                if contains_dot:  # 包含点（表名.字段名）
                    where_fields = [field.split('.')[-1] for field in where_fields if field.startswith(table_name + ".")]
                for where_field in where_fields:
                    Cardinality = count_column_value(table_name, where_field, mysql_settings, sample_size)
                    if Cardinality:
                        count_value = Cardinality[0]['count']
                        print(f"取出表 【{table_name}】 where条件字段 【{where_field}】 {sample_size} 条记录，重复的数据有：【{count_value}】 条，没有必要为该字段创建索引。")
                    else:
                        add_index_fields.append(where_field)

            if group_by_fields is not None and len(group_by_fields) != 0:
                contains_dot = any('.' in field for field in group_by_fields)
                if contains_dot:  # 包含点（表名.字段名）
                    group_by_fields = [field.split('.')[-1] for field in group_by_fields if field.startswith(table_name + ".")]
                for group_field in group_by_fields:
                    Cardinality = count_column_value(table_name, group_field, mysql_settings, sample_size)
                    if Cardinality:
                        count_value = Cardinality[0]['count']
                        print(f"取出表 【{table_name}】 group by条件字段 【{group_field}】 {sample_size} 条记录，重复的数据有：【{count_value}】 条，没有必要为该字段创建索引。")
                    else:
                        add_index_fields.append(group_field)

            if len(order_by_fields) != 0:
                contains_dot = any('.' in field for field in order_by_fields)
                if contains_dot:  # 包含点（表名.字段名）
                    order_by_fields = [field.split('.')[-1] for field in order_by_fields if field.startswith(table_name + ".")]
                for order_field in order_by_fields:
                    Cardinality = count_column_value(table_name, order_field, mysql_settings, sample_size)
                    if Cardinality:
                        count_value = Cardinality[0]['count']
                        print(f"取出表 【{table_name}】 order by条件字段 【{order_field}】 {sample_size} 条记录，重复的数据有：【{count_value}】 条，没有必要为该字段创建索引。")
                    else:
                        add_index_fields.append(order_field)

            if len(add_index_fields) == 0:
                if 'index_result' not in globals():
                    print("你的SQL太逆天，无需添加任何索引。")
                elif index_result:
                    print("你的SQL太逆天，无需添加任何索引。")
                else:
                    pass
            elif len(add_index_fields) == 1:
                index_name = add_index_fields[0]
                index_columns = add_index_fields[0]
                if row['key'] is None:
                    print(f"\033[93m建议添加索引：ALTER TABLE {table_name} ADD INDEX idx_{index_name}({index_columns});\033[0m")
                print(f"\n【{table_name}】表 【{index_columns}】字段，索引分析：")
                index_static = execute_index_query(mysql_settings, database=mysql_settings["database"], table_name=table_name, index_columns=index_columns)
                print(index_static)
            else:
                merged_name = '_'.join(add_index_fields)
                merged_columns  = ','.join(add_index_fields)
                if row['key'] is None:
                    print(f"\033[93m建议添加索引：ALTER TABLE {table_name} ADD INDEX idx_{merged_name}({merged_columns});\033[0m")
                print(f"\n【{table_name}】表 【{merged_columns}】字段，索引分析：")
                index_static = execute_index_query(mysql_settings, database=mysql_settings["database"], table_name=table_name, index_columns=merged_columns)
                print(index_static)

        # 判断表是否有别名，有别名的情况：
        if has_table_alias(table_aliases) is True:
            table_real_name = table_aliases[table_name]

            if len(where_fields) != 0:
                where_matching_fields = []
                for field in where_fields:
                    if field.startswith(table_real_name + '.'):
                        where_matching_fields.append(field.split('.')[1])
                for where_field in where_matching_fields:
                    Cardinality = count_column_value(table_real_name, where_field, mysql_settings, sample_size)
                    if Cardinality:
                        count_value = Cardinality[0]['count']
                        print(
                            f"取出表 【{table_real_name}】 where条件字段 【{where_field}】 {sample_size} 条记录，重复的数据有：【{count_value}】 条，没有必要为该字段创建索引。")
                    else:
                        add_index_fields.append(where_field)

            if group_by_fields is not None and len(group_by_fields) != 0:
                group_matching_fields = []
                for field in group_by_fields:
                    if field.startswith(table_real_name + '.'):
                        group_matching_fields.append(field.split('.')[1])
                for group_field in group_matching_fields:
                    Cardinality = count_column_value(table_real_name, group_field, mysql_settings, sample_size)
                    if Cardinality:
                        count_value = Cardinality[0]['count']
                        print(
                            f"取出表 【{table_name}】 group by条件字段 【{group_field}】 {sample_size} 条记录，重复的数据有：【{count_value}】 条，没有必要为该字段创建索引。")
                    else:
                        add_index_fields.append(group_field)

            if len(order_by_fields) != 0:
                order_matching_fields = []
                for field in order_by_fields:
                    if field.startswith(table_real_name + '.'):
                        order_matching_fields.append(field.split('.')[1])
                for order_field in order_matching_fields:
                    Cardinality = count_column_value(table_real_name, order_field, mysql_settings, sample_size)
                    if Cardinality:
                        count_value = Cardinality[0]['count']
                        print(f"取出表 【{table_name}】 order by条件字段 【{order_field}】 {sample_size} 条记录，重复的数据有：【{count_value}】 条，没有必要为该字段创建索引。")
                    else:
                        add_index_fields.append(order_field)

            if len(add_index_fields) == 0:
                if 'index_result' not in globals():
                    print("你的SQL太逆天，无需添加任何索引。")
                elif index_result:
                    print("你的SQL太逆天，无需添加任何索引。")
                else:
                    pass
            elif len(add_index_fields) == 1:
                index_name = add_index_fields[0]
                index_columns = add_index_fields[0]
                if row['key'] is None:
                    print(f"\033[93m建议添加索引：ALTER TABLE {table_real_name} ADD INDEX idx_{index_name}({index_columns});\033[0m")
                print(f"\n【{table_real_name}】表 【{index_columns}】字段，索引分析：")
                index_static = execute_index_query(mysql_settings, database=mysql_settings["database"], table_name=table_real_name, index_columns=index_columns)
                print(index_static)
            else:
                merged_name = '_'.join(add_index_fields)
                merged_columns  = ','.join(add_index_fields)
                if row['key'] is None:
                    print(f"\033[93m建议添加索引：ALTER TABLE {table_real_name} ADD INDEX idx_{merged_name}({merged_columns});\033[0m")
                print(f"\n【{table_real_name}】表 【{merged_columns}】字段，索引分析：")
                index_static = execute_index_query(mysql_settings, database=mysql_settings["database"], table_name=table_real_name, index_columns=merged_columns)
                print(index_static)
        
# 关闭游标和连接
cur.close()
conn.close()


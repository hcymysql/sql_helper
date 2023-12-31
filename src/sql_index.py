import textwrap
from tabulate import tabulate
import pymysql

def execute_index_query(mysql_settings, database, table_name, index_columns):
    index_columns = index_columns
    index_columns = index_columns.split(',')
    updated_columns = [f"'{column.strip()}'" for column in index_columns]
    final_columns = ', '.join(updated_columns)
    sql = f"SELECT TABLE_NAME,INDEX_NAME,COLUMN_NAME,CARDINALITY FROM information_schema.STATISTICS WHERE TABLE_SCHEMA = '{database}' AND TABLE_NAME = '{table_name}' AND COLUMN_NAME IN ({final_columns})"
    #print(sql)
    try:
        conn = pymysql.connect(**mysql_settings)
        cur = conn.cursor()
        cur.execute(sql)
        index_result = cur.fetchall()

        if not index_result:
            print(f"没有检测到 {table_name} 表 字段 {final_columns} 有索引。")

        # 提取列名
        e_column_names = [desc[0] for desc in cur.description]

        # 提取结果值并进行自动换行处理
        e_result_values = []
        for row in index_result:
            values = list(row.values())
            wrapped_values = [textwrap.fill(str(value), width=30) for value in values]
            e_result_values.append(wrapped_values)

        # 将结果格式化为表格（包含竖线）
        e_table = tabulate(e_result_values, headers=e_column_names, tablefmt="grid", numalign="left")

        return e_table

    except pymysql.err.ProgrammingError as e:
        print("MySQL 内部错误：",e)
        return None
    except Exception as e:
        print("MySQL 内部错误：",e)
        return None
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

#########################################################

def check_index_exist(mysql_settings, table_name, index_column):
    show_index_sql = f"show index from {table_name} where Column_name = '{index_column}'"
    try:
        conn = pymysql.connect(**mysql_settings)
        cur = conn.cursor()
        cur.execute(show_index_sql)
        index_result = cur.fetchall()

        #if not index_result:
            #print(f"没有检测到 {table_name} 表 字段 {final_columns} 有索引。")

        return index_result

    except pymysql.err.ProgrammingError as e:
        print("MySQL 内部错误：",e)
        return None
    except Exception as e:
        print("MySQL 内部错误：",e)
        return None
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

#########################################################

def check_index_exist_multi(mysql_settings, database, table_name, index_columns, index_number):
    index_columns = index_columns
    index_columns = index_columns.split(',')
    updated_columns = [f"'{column.strip()}'" for column in index_columns]
    final_columns = ', '.join(updated_columns)
    sql = f"SELECT TABLE_NAME,INDEX_NAME,COLUMN_NAME,CARDINALITY FROM information_schema.STATISTICS WHERE TABLE_SCHEMA = '{database}' AND TABLE_NAME = '{table_name}' AND COLUMN_NAME IN ({final_columns}) GROUP BY INDEX_NAME HAVING COUNT(INDEX_NAME) = {index_number}"
    #print(sql)
    try:
        conn = pymysql.connect(**mysql_settings)
        cur = conn.cursor()
        cur.execute(sql)
        index_result = cur.fetchall()

        if not index_result:
            return None

        return index_result

    except pymysql.err.ProgrammingError as e:
        print("MySQL 内部错误：",e)
        return None
    except Exception as e:
        print("MySQL 内部错误：",e)
        return None
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


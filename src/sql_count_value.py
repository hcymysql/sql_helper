import pymysql

def count_column_value(table_name, field_name, mysql_settings, sample_size):
    with pymysql.connect(**mysql_settings) as conn:
        with conn.cursor() as cursor:
            # 构造SQL查询语句
            sql = f"""
                SELECT COUNT(*) as count
                FROM (
                    SELECT {field_name}
                    FROM {table_name}
                    LIMIT 100000
                ) AS subquery
                GROUP BY {field_name}
                HAVING COUNT(*) >= {sample_size}/2;
            """

            cursor.execute(sql)

            results = cursor.fetchall()

    if results:
        # 如果有超过5万条的重复数据
        return results
    else:
        return False


import pymysql

def count_column_value(table_name, field_name, mysql_settings, sample_size):
    with pymysql.connect(**mysql_settings) as conn:
        with conn.cursor() as cursor:
            
            """
            在这个查询中，使用了CASE语句来判断数据行数是否小于100000。如果数据行数小于100000，则使用
            (SELECT COUNT(*) FROM {table_name}) / 2
            作为阈值，即表的实际大小除以2；否则使用 {sample_size} / 2 作为阈值。
            """
            
            sql = f"""
            SELECT COUNT(*) as count
            FROM (
                SELECT {field_name}
                FROM {table_name}
                LIMIT {sample_size}
            ) AS subquery
            GROUP BY {field_name}
            HAVING COUNT(*) >= CASE WHEN (SELECT COUNT(*) FROM {table_name} LIMIT {sample_size}) < {sample_size} 
            THEN (SELECT COUNT(*) FROM {table_name}) / 2 ELSE {sample_size} / 2 END;
            """
            #print(sql)
            cursor.execute(sql)

            results = cursor.fetchall()

    if results:
        # 如果有超过半数的重复数据
        return results
    else:
        return False



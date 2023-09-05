import sqlparse

def parse_where_condition(sql, column):
    parsed = sqlparse.parse(sql)
    stmt = parsed[0]

    where_column = ""
    where_expression = ""
    where_value = ""
    where_clause = ""
    found = False
    result = ""

    for token in stmt.tokens:
        if isinstance(token, sqlparse.sql.Where):
            where_clause = token.value
            conditions = []
            for cond_tok in token.tokens:
                if isinstance(cond_tok, sqlparse.sql.Comparison):
                    left_token = cond_tok.left.value.strip()
                    if column == left_token:
                        #return f"比较运算符: {cond_tok.value.strip()}"
                        return cond_tok.value.strip()

                if isinstance(cond_tok, sqlparse.sql.Identifier) and cond_tok.value == column:
                    found = True

                if found:
                    if isinstance(cond_tok, sqlparse.sql.Token) and cond_tok.value.upper() in ["OR","AND"]:
                        break
                    else:
                        result += cond_tok.value

                if isinstance(cond_tok, sqlparse.sql.Parenthesis) and found:
                    break

    if len(result) != 0:
        #return f"逻辑运算符: {result.strip()}"
        return result.strip()
    else:
        #return "没有找到该字段的条件表达式"
        return None

'''
# 测试示例
sql = """
SELECT req.id
  from cc_service_request req INNER JOIN cc_customer_info cus on req.customer_id=cus.id
  INNER JOIN cc_user us on req.service_user_id=us.id
  LEFT JOIN cc_service_request_change_log srcl ON req.id = srcl.service_id
  WHERE 1 = 1 AND req.delete_flag = 0
  AND DATE_FORMAT(req.last_service_time, '%Y-%m-%d  %H:%i:%s')>= DATE_FORMAT('2023-05-04 00:00:00', '%Y-%m-%d  %H:%i:%s')   
  AND DATE_FORMAT(req.last_service_time, '%Y-%m-%d  %H:%i:%s')<= DATE_FORMAT('2023-05-04 23:59:59', '%Y-%m-%d  %H:%i:%s')   
  and us.depart_id in (10,52,56,57,60,62,63,64,65,66,68,70,79,96,97,98,10)
  ORDER BY id desc
  limit 0,20
"""
column = "req.delete_flag"
result = parse_where_condition(sql, column)
print(result)  # 输出: 比较运算符: t.create_time >= '2023-05-01 00:00:00'
'''

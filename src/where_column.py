"""
实验分支 - 识别WHERE条件表达式（通过指定字段名，来识别它的条件表达式）
这是一个未合并到主分支的功能，仅用于测试。
"""
import sqlparse

sql = """
SELECT 
  t.* 
FROM 
  hechunyang as t
WHERE 
  1 = 1 
  AND t.request_id = '1111111111111' 
  AND t.create_time >= '2023-05-01 00:00:00'
  AND t.uid in (1,2,3)
  AND t.cid is not null
  OR t.gid is null
ORDER BY 
  id desc 
limit 
  0, 
  20
"""

parsed = sqlparse.parse(sql)
stmt = parsed[0]

column = "t.create_time"

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
            #print(type(cond_tok), cond_tok)
            if isinstance(cond_tok, sqlparse.sql.Comparison):
                left_token = cond_tok.left.value.strip()
                if column == left_token:
                    print(f"比较运算符: {cond_tok.value.strip()}")

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
    print("-" * 55)
    print(f"逻辑运算符: {result.strip()}")



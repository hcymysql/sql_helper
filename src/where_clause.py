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


def parse_where_condition_full(sql):
    parsed = sqlparse.parse(sql)
    stmt = parsed[0]

    where_clause = ""
    found = False

    for token in stmt.tokens:
        if found:
            where_clause += token.value
        if isinstance(token, sqlparse.sql.Where):
            found = True
            where_clause += token.value

    return where_clause.strip() if where_clause else None


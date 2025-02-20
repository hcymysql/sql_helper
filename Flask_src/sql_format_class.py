import sqlparse

class SQLFormatter:
    def format_sql(self, sql_query):
        """
        格式化 SQL 查询语句
        """
        formatted_sql = sqlparse.format(sql_query, reindent=True, keyword_case='upper')

        return formatted_sql



import sys, re
import textwrap
from tabulate import tabulate
import pymysql
from sql_metadata import Parser
from sql_format_class import SQLFormatter
from sql_alias import has_table_alias
from sql_count_value import count_column_value, count_column_clause_value
from sql_index import execute_index_query, check_index_exist, check_index_exist_multi
from where_clause import *
from sql_extra import *
import yaml
import argparse
from sql_deepseek import *
from flask import Flask, request, render_template

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['JSON_SORT_KEYS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['DEFAULT_CHARSET'] = 'utf-8'

def analyze_sql(sql_query, db_config, sample_size=100000):
    mysql_settings = {
        "host": db_config["host"],
        "port": db_config["port"],
        "user": db_config["user"],
        "passwd": db_config["passwd"],
        "database": db_config["database"],
        "cursorclass": pymysql.cursors.DictCursor,
        "charset": 'utf8mb4'
    }

    try:
        formatted_sql = SQLFormatter().format_sql(sql_query)
    except UnicodeDecodeError as e:
        print(f"格式化 SQL 时出错: {e}, sql_query: {sql_query}")
        return {"error": f"格式化 SQL 时出错: {e}", "is_processing": False}

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
            return {"error": "sql_helper工具仅支持select语句", "is_processing": False}
    except Exception as e:
        return {"error": f"解析 SQL 出现语法错误：{str(e)}", "is_processing": False}

    conn = None
    try:
        conn = pymysql.connect(**mysql_settings)
        cur = conn.cursor()

        sql = f"EXPLAIN {sql_query}"
        try:
            cur.execute(sql)
        except pymysql.err.ProgrammingError as e:
            return {"error": f"MySQL 内部错误：{e}", "is_processing": False}
        except Exception as e:
            return {"error": f"MySQL 内部错误：{e}", "is_processing": False}
        explain_result = cur.fetchall()

        e_column_names = list(explain_result[0].keys())
        e_result_values = []
        for row in explain_result:
            values = [str(value) for value in row.values()]  # 直接转为字符串
            e_result_values.append(values)
        e_table = tabulate(e_result_values, headers=e_column_names, tablefmt="html", numalign="left")
    except Exception as e:
        return {"error": f"执行 EXPLAIN 或处理结果时出错: {e}", "is_processing": False}
    finally:
        if conn:
            conn.close()

    index_suggestions = []
    contains_dot = False
    if len(where_fields) == 0:
        index_suggestions.append(f"你的SQL没有where条件.")
    else:
        contains_dot = any('.' in field for field in where_fields)

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
                try:
                    show_index_sql = f"show index from {table_name} where Column_name = '{on_column}'"
                    conn = pymysql.connect(**mysql_settings)
                    cur = conn.cursor()
                    cur.execute(show_index_sql)
                    index_result = cur.fetchall()
                    if not index_result:
                        suggestion_text = "join联表查询，on关联字段必须增加索引！\n"
                        suggestion_text += f"<span style=\"color: red;\">\n需要添加索引：ALTER TABLE {table_name} ADD INDEX idx_{on_column}({on_column});</span>\n"
                        suggestion_text += f"【{table_name}】表 【{on_column}】字段，索引分析：\n"
                        index_static = execute_index_query(mysql_settings, database=mysql_settings["database"],
                                                           table_name=table_name, index_columns=on_column)
                        suggestion_text += index_static + "\n"
                        index_suggestions.append(suggestion_text)
                except Exception as e:
                    print(f"join查询分析出错: {e}")
                    index_suggestions.append(f"join查询分析出错: {e}")
                finally:
                    if conn:
                        conn.close()

    for row in explain_result:
        # 修改处：防止 table_name 为 None
        #table_name = row.get('table', '')  # 使用 get() 设置默认值为空字符串
        table_name = row.get('table') or ''
        if table_name.lower().startswith('<derived'):
            table_name = ""
        if table_name == "":
            continue

        add_index_fields = []
        if (len(join_fields) != 0 and ((row['type'] == 'ALL' and row['key'] is None) or int(row['rows']) >= 1)) or \
           (len(join_fields) == 0 and ((row['type'] == 'ALL' and row['key'] is None) or int(row['rows']) >= 1000)):
            if has_table_alias(table_aliases) is False and contains_dot is False:
                if len(where_fields) != 0:
                    for where_field in where_fields:
                        where_clause_value = parse_where_condition(formatted_sql, where_field)
                        if where_clause_value is not None:
                            where_clause_value = where_clause_value.replace('\n', '').replace('\r', '')
                            where_clause_value = re.sub(r'\s+', ' ', where_clause_value)
                            where_clause_value = re.sub(r'\s+', ' ', where_clause_value)
                            Cardinality = count_column_clause_value(table_name, where_field, where_clause_value, mysql_settings, sample_size)
                        else:
                            Cardinality = count_column_value(table_name, where_field, mysql_settings, sample_size)
                        if Cardinality:
                            count_value = Cardinality[0]['count']
                            if where_clause_value is not None:
                                suggestion_text = f"\n取出表 【{table_name}】 where条件表达式 【{where_clause_value}】 {sample_size} 条记录，重复的数据有：【{count_value}】 条，没有必要为该字段创建索引。\n"
                                index_suggestions.append(suggestion_text)
                            else:
                                suggestion_text = f"\n取出表 【{table_name}】 where条件字段 【{where_field}】 {sample_size} 条记录，重复的数据有：【{count_value}】 条，没有必要为该字段创建索引。\n"
                                index_suggestions.append(suggestion_text)
                        else:
                            add_index_fields.append(where_field)

                if group_by_fields is not None and len(group_by_fields) != 0:
                    for group_field in group_by_fields:
                        Cardinality = count_column_value(table_name, group_field, mysql_settings, sample_size)
                        if Cardinality:
                            count_value = Cardinality[0]['count']
                            suggestion_text = f"\n取出表 【{table_name}】 group by条件字段 【{group_field}】 {sample_size} 条记录，重复的数据有：【{count_value}】 条，没有必要为该字段创建索引。\n"
                            index_suggestions.append(suggestion_text)
                        else:
                            add_index_fields.append(group_field)

                if len(order_by_fields) != 0:
                    for order_field in order_by_fields:
                        Cardinality = count_column_value(table_name, order_field, mysql_settings, sample_size)
                        if Cardinality:
                            count_value = Cardinality[0]['count']
                            suggestion_text = f"\n取出表 【{table_name}】 order by条件字段 【{order_field}】 {sample_size} 条记录，重复的数据有：【{count_value}】 条，没有必要为该字段创建索引。\n"
                            index_suggestions.append(suggestion_text)
                        else:
                            add_index_fields.append(order_field)

                add_index_fields = list(dict.fromkeys(add_index_fields).keys())

                if len(add_index_fields) == 0:
                    if not index_suggestions:
                        index_suggestions.append(f"\n<span style=\"color: green; font-weight: bold;\">→ 【{table_name}】 表，无需添加任何索引。</span>\n")
                    else:
                        index_suggestions.append(f"\n<span style=\"color: green; font-weight: bold;\">→ 【{table_name}】 表，无需添加任何索引。</span>\n")
                elif len(add_index_fields) == 1:
                    index_name = add_index_fields[0]
                    index_columns = add_index_fields[0]
                    try:
                        conn = pymysql.connect(**mysql_settings)
                        cur = conn.cursor()
                        index_result = check_index_exist(mysql_settings, table_name=table_name, index_column=index_columns)
                        if not index_result:
                            suggestion_text = ""
                            if row['key'] is None:
                                suggestion_text += f"<span style=\"color: #FFA500;\">\n建议添加索引：ALTER TABLE {table_name} ADD INDEX idx_{index_name}({index_columns});</span>\n"
                            elif row['key'] is not None and row['rows'] >= 1:
                                suggestion_text += f"<span style=\"color: #FFA500;\">\n建议添加索引：ALTER TABLE {table_name} ADD INDEX idx_{index_name}({index_columns});</span>\n"
                            suggestion_text += f"\n【{table_name}】表 【{index_columns}】字段，索引分析：\n"
                            index_static = execute_index_query(mysql_settings, database=mysql_settings["database"],
                                                               table_name=table_name, index_columns=index_columns)
                            suggestion_text += index_static + "\n"
                            index_suggestions.append(suggestion_text)
                        else:
                            suggestion_text = f"\n<span style=\"color: green; font-weight: bold;\">→ 【{table_name}】表 【{index_columns}】字段，索引已经存在，无需添加任何索引。</span>\n"
                            suggestion_text += f"\n【{table_name}】表 【{index_columns}】字段，索引分析：\n"
                            index_static = execute_index_query(mysql_settings, database=mysql_settings["database"],
                                                               table_name=table_name, index_columns=index_columns)
                            suggestion_text += index_static + "\n"
                            index_suggestions.append(suggestion_text)
                    except Exception as e:
                        print(f"单个索引分析出错: {e}")
                        index_suggestions.append(f"单个索引分析出错: {e}")
                    finally:
                        if conn:
                            conn.close()

                else:
                    merged_name = '_'.join(add_index_fields)
                    merged_columns = ','.join(add_index_fields)
                    try:
                        conn = pymysql.connect(**mysql_settings)
                        cur = conn.cursor()
                        index_result_list = check_index_exist_multi(mysql_settings, database=mysql_settings["database"],
                                                                    table_name=table_name, index_columns=merged_columns,
                                                                    index_number=len(add_index_fields))
                        if index_result_list is None:
                            suggestion_text = ""
                            if row['key'] is None:
                                suggestion_text += f"<span style=\"color: #FFA500;\">\n建议添加索引：ALTER TABLE {table_name} ADD INDEX idx_{merged_name}({merged_columns});</span>\n"
                            elif row['key'] is not None and row['rows'] >= 1:
                                suggestion_text += f"<span style=\"color: #FFA500;\">\n建议添加索引：ALTER TABLE {table_name} ADD INDEX idx_{merged_name}({merged_columns});</span>\n"
                            suggestion_text += f"\n【{table_name}】表 【{merged_columns}】字段，索引分析：\n"
                            index_static = execute_index_query(mysql_settings, database=mysql_settings["database"],
                                                               table_name=table_name, index_columns=merged_columns)
                            suggestion_text += index_static + "\n"
                            index_suggestions.append(suggestion_text)
                        else:
                            suggestion_text = f"\n<span style=\"color: green; font-weight: bold;\">→ 【{table_name}】表 【{merged_columns}】字段，联合索引已经存在，无需添加任何索引。</span>\n"
                            suggestion_text += f"\n【{table_name}】表 【{merged_columns}】字段，索引分析：\n"
                            index_static = execute_index_query(mysql_settings, database=mysql_settings["database"],
                                                               table_name=table_name, index_columns=merged_columns)
                            suggestion_text += index_static + "\n"
                            index_suggestions.append(suggestion_text)
                    except Exception as e:
                        print(f"联合索引分析出错: {e}")
                        index_suggestions.append(f"联合索引分析出错: {e}")
                    finally:
                        if conn:
                            conn.close()

            if has_table_alias(table_aliases) is True or contains_dot is True:
                if has_table_alias(table_aliases) is True:
                    try:
                        table_real_name = table_aliases[table_name]
                    except KeyError:
                        if table_name.startswith('<union'):
                            table_real_name = ""
                else:
                    table_real_name = table_name

                if table_real_name != "":
                    if len(where_fields) != 0:
                        where_matching_fields = []
                        for field in where_fields:
                            if field.startswith(table_real_name + '.'):
                                where_matching_fields.append(field.split('.')[1])

                        for where_field in where_matching_fields:
                            talia_clause = table_name + '.' + where_field
                            where_clause_value = parse_where_condition(formatted_sql, talia_clause)
                            if where_clause_value is not None:
                                where_clause_value = where_clause_value.replace('\n', '').replace('\r', '')
                                where_clause_value = re.sub(r'\s+', ' ', where_clause_value)
                                prefix = where_clause_value.split('.')[0]
                                where_clause_value = where_clause_value.replace(prefix + '.', '')
                                if "." in where_clause_value:
                                    Cardinality = count_column_value(table_real_name, where_field, mysql_settings, sample_size)
                                else:
                                    Cardinality = count_column_clause_value(table_real_name, where_field, where_clause_value, mysql_settings, sample_size)
                            else:
                                Cardinality = count_column_value(table_real_name, where_field, mysql_settings, sample_size)
                            if Cardinality:
                                count_value = Cardinality[0]['count']
                                if where_clause_value is not None:
                                    suggestion_text = f"\n取出表 【{table_real_name}】 where条件表达式 【{where_clause_value}】 {sample_size} 条记录，重复的数据有：【{count_value}】 条，没有必要为该字段创建索引。\n"
                                    index_suggestions.append(suggestion_text)
                                else:
                                    suggestion_text = f"\n取出表 【{table_real_name}】 where条件字段 【{where_field}】 {sample_size} 条记录，重复的数据有：【{count_value}】 条，没有必要为该字段创建索引。\n"
                                    index_suggestions.append(suggestion_text)
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
                                suggestion_text = f"\n取出表 【{table_real_name}】 group by条件字段 【{group_field}】 {sample_size} 条记录，重复的数据有：【{count_value}】 条，没有必要为该字段创建索引。\n"
                                index_suggestions.append(suggestion_text)
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
                                suggestion_text = f"\n取出表 【{table_real_name}】 order by条件字段 【{order_field}】 {sample_size} 条记录，重复的数据有：【{count_value}】 条，没有必要为该字段创建索引。\n"
                                index_suggestions.append(suggestion_text)
                            else:
                                add_index_fields.append(order_field)

                    add_index_fields = list(dict.fromkeys(add_index_fields).keys())

                    if len(add_index_fields) == 0:
                        index_suggestions.append(f"\n<span style=\"color: green; font-weight: bold;\">→ 【{table_real_name}】 表，无需添加任何索引。</span>\n")
                    elif len(add_index_fields) == 1:
                        index_name = add_index_fields[0]
                        index_columns = add_index_fields[0]
                        try:
                            conn = pymysql.connect(**mysql_settings)
                            cur = conn.cursor()
                            index_result = check_index_exist(mysql_settings, table_name=table_real_name, index_column=index_columns)
                            if not index_result:
                                suggestion_text = ""
                                if row['key'] is None:
                                    suggestion_text += f"<span style=\"color: #FFA500;\">\n建议添加索引：ALTER TABLE {table_real_name} ADD INDEX idx_{index_name}({index_columns});</span>\n"
                                elif row['key'] is not None and row['rows'] >= 1:
                                    suggestion_text += f"<span style=\"color: #FFA500;\">\n建议添加索引：ALTER TABLE {table_real_name} ADD INDEX idx_{index_name}({index_columns});</span>\n"
                                suggestion_text += f"\n【{table_real_name}】表 【{index_columns}】字段，索引分析：\n"
                                index_static = execute_index_query(mysql_settings, database=mysql_settings["database"],
                                                                   table_name=table_real_name, index_columns=index_columns)
                                suggestion_text += index_static + "\n"
                                index_suggestions.append(suggestion_text)
                            else:
                                suggestion_text = f"\n<span style=\"color: green; font-weight: bold;\">→ 【{table_real_name}】表 【{index_columns}】字段，索引已经存在，无需添加任何索引。</span>\n"
                                suggestion_text += f"\n【{table_real_name}】表 【{index_columns}】字段，索引分析：\n"
                                index_static = execute_index_query(mysql_settings, database=mysql_settings["database"],
                                                                   table_name=table_real_name, index_columns=index_columns)
                                suggestion_text += index_static + "\n"
                                index_suggestions.append(suggestion_text)
                        except Exception as e:
                            print(f"单个别名表索引分析出错: {e}")
                            index_suggestions.append(f"单个别名表索引分析出错: {e}")
                        finally:
                            if conn:
                                conn.close()
                    else:
                        merged_name = '_'.join(add_index_fields)
                        merged_columns = ','.join(add_index_fields)
                        try:
                            conn = pymysql.connect(**mysql_settings)
                            cur = conn.cursor()
                            index_result_list = check_index_exist_multi(mysql_settings, database=mysql_settings["database"],
                                                                        table_name=table_real_name, index_columns=merged_columns,
                                                                        index_number=len(add_index_fields))
                            if index_result_list is None:
                                suggestion_text = ""
                                if row['key'] is None:
                                    suggestion_text += f"<span style=\"color: #FFA500;\">\n建议添加索引：ALTER TABLE {table_real_name} ADD INDEX idx_{merged_name}({merged_columns});</span>\n"
                                elif row['key'] is not None and row['rows'] >= 1:
                                    suggestion_text += f"<span style=\"color: #FFA500;\">\n建议添加索引：ALTER TABLE {table_real_name} ADD INDEX idx_{merged_name}({merged_columns});</span>\n"
                                suggestion_text += f"\n【{table_real_name}】表 【{merged_columns}】字段，索引分析：\n"
                                index_static = execute_index_query(mysql_settings, database=mysql_settings["database"],
                                                                   table_name=table_real_name, index_columns=merged_columns)
                                suggestion_text += index_static + "\n"
                                index_suggestions.append(suggestion_text)
                            else:
                                suggestion_text = f"\n<span style=\"color: green; font-weight: bold;\">→ 【{table_real_name}】表 【{merged_columns}】字段，联合索引已经存在，无需添加任何索引。</span>\n"
                                suggestion_text += f"\n【{table_real_name}】表 【{merged_columns}】字段，索引分析：\n"
                                index_static = execute_index_query(mysql_settings, database=mysql_settings["database"],
                                                                   table_name=table_real_name, index_columns=merged_columns)
                                suggestion_text += index_static + "\n"
                                index_suggestions.append(suggestion_text)
                        except Exception as e:
                            print(f"联合别名表索引分析出错: {e}")
                            index_suggestions.append(f"联合别名表索引分析出错: {e}")
                        finally:
                            if conn:
                                conn.close()

    extra_suggestions = []
    where_clause = parse_where_condition_full(formatted_sql)
    if where_clause:
        like_r, like_expression = check_percent_position(where_clause)
        if like_r is True:
            extra_suggestions.append(f"like模糊匹配，百分号在首位，【{like_expression}】是不能用到索引的，例如like '%张三%'，可以考虑改成like '张三%'，这样是可以用到索引的，如果业务上不能改，可以考虑用全文索引。\n")

        function_r = extract_function_index(where_clause)
        if function_r is not False:
            extra_suggestions.append(f"索引列使用了函数作计算：【{function_r}】，会导致索引失效。"
                                     f"如果你是MySQL 8.0可以考虑创建函数索引；如果你是MySQL 5.7，你要更改你的SQL逻辑了。\n")

    try:
        # 开始处理 AI 优化，设置 is_processing=True
        ai_suggestions = optimize_sql(formatted_sql)
        if not isinstance(ai_suggestions, str):
            ai_suggestions = str(ai_suggestions)
        ai_suggestions = re.sub(r'```html\s*|\s*```', '', ai_suggestions, flags=re.MULTILINE).strip()
    except Exception as e:
        ai_suggestions = f"调用 AI 优化出错: {e}"
        print(f"调用 AI 优化出错: {e}")

    return {
        "formatted_sql": formatted_sql,
        "explain_table": e_table,
        "index_suggestions": "".join(index_suggestions),
        "extra_suggestions": "".join(extra_suggestions),
        "ai_suggestions": ai_suggestions,
        "no_suggestions": not index_suggestions and not extra_suggestions and not ai_suggestions,
        "is_processing": False  # 处理完成
    }

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        sql_query = request.form.get("sql_query")
        host = request.form.get("host")
        port = request.form.get("port", type=int, default=3306)
        user = request.form.get("user")
        password = request.form.get("password")
        database = request.form.get("database")

        db_config = {}
        config_source = ""

        if not all([host, user, password, database]):
            return render_template("index.html", error="请提供完整的 MySQL 数据库连接信息 (请手动填写所有数据库参数).",
                                   sql_query=sql_query,
                                   host=host, port=port, user=user, database=database,
                                   is_processing=False)

        db_config = {
            "host": host,
            "port": port,
            "user": user,
            "passwd": password,
            "database": database
        }
        config_source = "params"

        # 在分析开始时，显示加载动画
        analysis_result = analyze_sql(sql_query, db_config)

        if "error" in analysis_result:
            return render_template("index.html", error=analysis_result["error"],
                                   sql_query=sql_query,
                                   host=host, port=port, user=user, database=database,
                                   config_source=config_source,
                                   is_processing=False)

        return render_template("index.html",
                               formatted_sql=analysis_result["formatted_sql"],
                               explain_table=analysis_result["explain_table"],
                               index_suggestions=analysis_result["index_suggestions"],
                               extra_suggestions=analysis_result["extra_suggestions"],
                               ai_suggestions=analysis_result["ai_suggestions"],
                               no_suggestions=analysis_result["no_suggestions"],
                               sql_query=sql_query,
                               host=host, port=port, user=user, database=database,
                               config_source=config_source,
                               is_processing=False)  # 处理完成

    return render_template("index.html", is_processing=False)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)

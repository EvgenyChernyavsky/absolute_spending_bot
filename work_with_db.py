import calendar as cal
from config import States
import psycopg2
import os

# здесь нужен адрес базы данных Postgres. Я беру его из переменной на Heroku, если нужна сторонняя БД, то нужно просто
# указать адрес
DATABASE_URL = os.environ['DATABASE_URL']

# функция вставляет основную инфу о пользователе
def insert_general_info(user_id, month, year, annual_earnings, annual_spendings, planning_to_save):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()
    information = (user_id, month, year, annual_earnings, annual_spendings,
                   annual_earnings - annual_spendings - planning_to_save, 0, planning_to_save)
    cursor.execute("INSERT INTO public.general_info VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", information)
    conn.commit()
    cursor.close()
    conn.close()

# функция меняет основные данные о пользователе
def update_general_info (user_id, month, year, annual_earnings, annual_spendings, planning_to_save):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()
    information = (annual_earnings, annual_spendings,
                   annual_earnings - annual_spendings - planning_to_save, planning_to_save, user_id, month, year)
    cursor.execute('UPDATE public.general_info '
                   'SET annual_earning = %s, anual_spending = %s, money_for_month = %s, planning_to_save = %s '
                   'WHERE user_id = %s AND gen_month = %s AND gen_year = %s', information)
    conn.commit()
    cursor.close()
    conn.close()


# функция вставляет данные в лог трат
def insert_spending(user_id, day, month, year, spending, category):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()
    information = (user_id, day, month, year, spending, category)
    cursor.execute("INSERT INTO public.spendings_log VALUES (%s, %s, %s, %s, %s, %s)", information)
    conn.commit()
    cursor.close()
    conn.close()


# функция возвращает основную информацию о пользователе (в виде листа)
def get_general_info(user_id, month, year):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()
    sql = 'SELECT annual_earning, anual_spending, money_for_month, spend_in_month, planning_to_save FROM public.general_info ' \
          'WHERE user_id = %s AND gen_month = %s AND gen_year = %s'
    cursor.execute(sql, (user_id, month, year))
    general_info = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    if general_info == None:
        return None
    return general_info  # 0 - доход за месяц, 1 - обязательные траты за месяц, 2 - оставшиеся деньги на месяц, 3 -
    # потрачено за месяц, 4 - планируется отложить за месяц

# функция возвращает 5 последних трат
def get_last_spendings(user_id, spending_month, spending_year):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()
    sql = """
        SELECT spending_day, spending_month, spending_year, spending, category 
        FROM public.spendings_log
        WHERE user_id=%s AND spending_month = %s AND spending_year=%s
        ORDER BY spending_day DESC
        LIMIT 5
    """
    cursor.execute(sql, (user_id, spending_month, spending_year))
    last_spendings = cursor.fetchall()
    conn.commit()
    cursor.close()
    conn.close()
    if last_spendings == []:
        return None
    return last_spendings

# функция заворачивает 5 последних трат в красивый ответ (на выходе - строка)
def last5_answer(user_id, spending_month, spending_year):
    last_spendings = get_last_spendings(user_id, spending_month, spending_year)
    if last_spendings is None:
        return None
    result_line = 'Ваши последние траты:\n'
    for element in last_spendings:
        new_line = str(element[0]) + '.'+ str(element[1]) + '.' + str(element[2]) \
                   + ' было потрачено ' + str(element[3]) + ' р. на категорию "' + str(element[4]) + '"\n'
        result_line += new_line
    return result_line

# функция забирает все категории и потраченное на них
def get_all_categories(user_id, month, year):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()
    sql = """
    SELECT category, cat_spend
    FROM public.category_analysis
    WHERE cat_year = %s AND cat_month = %s AND user_id = %s
    ORDER BY cat_spend DESC
    """
    cursor.execute(sql, (year, month, user_id))
    all_categ = cursor.fetchall()
    conn.commit()
    cursor.close()
    conn.close()
    if all_categ == []:
        return None
    return all_categ

# функция возвращает топ-5 категорий трат за месяц и их сумму
def get_top5_cat(user_id, month, year):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()
    sql = """
            SELECT category, cat_spend FROM public.category_analysis
            WHERE cat_year = %s AND cat_month = %s AND user_id = %s
            ORDER BY cat_spend DESC
            LIMIT 5;
            """
    cursor.execute(sql, (year, month, user_id))
    top_5_cats = cursor.fetchall()
    conn.commit()
    cursor.close()
    conn.close()
    if top_5_cats == []:
        return None
    return top_5_cats

# функция заворачивает топ-5 в красивую строку с ответом (на выходе - строка)
def top5_cat_answer(user_id, month, year):
    answer = get_top5_cat(user_id, month, year)
    if answer is None:
        return None
    result_line = 'ТОП-5 трат по категориям за месяц:\n'
    for element in answer:
        new_line = str(element[1]) + ' р. - категория "' + str(element[0]) + '"\n'
        result_line += new_line
    return result_line

# Функция принимает параметры и возвращает таблицу, где расписаны траты на каждый день месяца и сальдо
def get_spendings_per_day(user_id, month, year):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()
    sql = """
            SELECT spen_day, spending FROM public.spendings_per_day
            WHERE user_id = %s AND spen_month = %s AND spen_year = %s
            ORDER BY spen_day;
            """
    cursor.execute(sql, (user_id, month, year))
    # получаем данные за каждый день из бд (индекс 0 - день, индекс 1 - трата за день)
    spendings_per_day = cursor.fetchall()
    conn.commit()
    cursor.close()
    conn.close()
    if spendings_per_day == None:
        return None
    spendings_per_day = list(map(list, spendings_per_day))
    # считаем сколько дней в месяце
    days_in_month = int((cal.monthrange(year, month))[1])
    # создаем пустую таблицу с датами в месяце и 0 трат
    spendings_table = [[i, 0] for i in range(1, days_in_month + 1)]
    # заполняем эту таблицу данными
    for index, item in enumerate(spendings_table):
        for element in spendings_per_day:
            if item[0] == element[0]:
                spendings_table[index] = element
    # считаем сколько среднее в день
    planned_per_day = round(get_general_info(user_id, month, year)[2] / days_in_month)
    # делаем прибавляем к имеющейся таблице бюджет и сальдо
    for i in range(len(spendings_table)):
        if i == 0:
            budjet = planned_per_day
            saldo = budjet - spendings_table[0][1]
        else:
            budjet = saldo + planned_per_day
            saldo = budjet - spendings_table[i][1]
        spendings_table[i].append(budjet)
        spendings_table[i].append(saldo)
    return spendings_table # Таблица в виде [(день1, трата, бюджет на день, сальдо), ... ]

# Функция забирает категории, из лога трат по каждому дню месяца
def get_categories_per_day(user_id, month, year):
    # забираем данные по категориям и дням
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()
    sql = """
            SELECT spending_day, category FROM public.spendings_log
            WHERE user_id=%s AND spending_month=%s AND spending_year=%s
            ORDER BY spending_day
            """
    cursor.execute(sql, (user_id, month, year))
    all_categories_in_days = cursor.fetchall()
    conn.commit()
    cursor.close()
    conn.close()
    if all_categories_in_days == None:
        return None
    # считаем сколько дней в месяце
    days_in_month = (cal.monthrange(year, month))[1]
    # создаем таблицу с днями недели и пустым местом для категорий
    categories_per_day = [[i, 'не тратил'] for i in range(1, days_in_month + 1)]
    for index, element in enumerate(categories_per_day):
        for item in all_categories_in_days:
            if item[0] == element[0]:
                if categories_per_day[index][1] == 'не тратил':
                    categories_per_day[index][1] = item[1] + ', '
                else:
                    categories_per_day[index][1] = categories_per_day[index][1] + item[1] + ', '
    return categories_per_day

# функция соединяет таблицу из spendings_per_pay с category_per_day, добавляет туда анализ категорий
def create_full_table(user_id, month, year):
    # получаем всю необходимую информацию
    spending_per_day = get_spendings_per_day(user_id, month, year)
    category_per_day = get_categories_per_day(user_id, month, year)
    all_categories = get_all_categories(user_id, month, year)
    # проверяем на отсутствие пустых выборок
    if spending_per_day is None or category_per_day is None or all_categories is None:
        return None
    # если ничего пустого нет, запускаем цикл, добавляя в spending_per_day категории, на которые были потрачены деньги
    # в течении дня
    for i in range(len(spending_per_day)):
        spending_per_day[i].insert(2, category_per_day[i][1])
    # создаем название файла
    table_name = '{}_analysis_for_{}_{}.xlsx'.format(user_id, month, year)
    file_name = '{}_analysis_for_{}_{}.xlsx'.format(user_id, month, year)
    import xlsxwriter
    # создаем эксель-файл и книгу в нем
    workbook = xlsxwriter.Workbook(table_name, {'in_memory': True})
    worksheet = workbook.add_worksheet('Data')
    # текст для заголовка первой строки
    header_text = ['День', 'Потрачено за день', 'На что потрачено', 'Бюджет на день', 'Сальдо ']
    row = 0
    col = 0
    # создаем жирный стиль
    bold = workbook.add_format({'bold': True, })
    # записываем заголовок таблицы в первую строку, перебирая колонки
    for element in header_text:
        worksheet.write(0, col, element, bold)
        col += 1
    row = 1
    # записываем значения в таблицу, перебирая ряды
    for day, spend_for_day, cat, budjet, saldo in spending_per_day:
        worksheet.write(row, 0, day)
        worksheet.write(row, 1, spend_for_day)
        worksheet.write(row, 2, cat)
        worksheet.set_column(2, 2, len(cat))
        worksheet.write(row, 3, budjet)
        worksheet.write(row, 4, saldo)
        row += 1
    row = 1
    # создаем еще заголовки и записываем их
    worksheet.write(0, 6, 'Категория', bold)
    worksheet.write(0, 7, 'Потрачено на категорию', bold)
    worksheet.set_column(7,7, len('Потрачено на категорию'))
    # записываем статистику по категориям в таблицу
    for category, spend_for_category in all_categories:
        worksheet.write(row, 6, category)
        worksheet.write(row, 7, spend_for_category)
        row += 1
    # создаем диаграмму
    cat_chart = workbook.add_chart({'type': 'column'})
    cat_chart.add_series({'name':' ',
        'categories': ['Data', 1, 6, len(all_categories), 6],
        'values': ['Data', 1, 7, len(all_categories), 7],
    })
    cat_chart.set_title({'name': 'График категорий трат'})
    cat_chart.set_x_axis({'name': 'Категории'})
    cat_chart.set_y_axis({'name': 'Сумма, р.'})
    cat_chart.set_style(11)
    worksheet.insert_chart('J2', cat_chart, {'x_offset': 10, 'y_offset': 10})
    # сохраняем готовый файл в папке с проектом
    workbook.close()
    return file_name



# функция показывает инфу о юзере за сегодня
def today_info(user_id, day, month, year):
    table = get_spendings_per_day(user_id, month, year)
    if table is None:
        return None
    if table[day-1][3] < 0:
        line = 'Сегодня вы потратили {} р. Допустимо было потратить {} р. Вы ушли в минус на {}. Осторожнее!'.format(
            table[day - 1][1], table[day - 1][2], abs(table[day-1][3]))
    else:
        line = 'Сегодня вы потратили {} р. Допустимо потратить {} р. Eщe можно потратить {} р.'.format(
            table[day - 1][1], table[day - 1][2], abs(table[day-1][3]))
    return line


# Пытаемся узнать из базы «состояние» пользователя
def get_current_state(user_id):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()
    sql = 'SELECT state FROM public.user_state WHERE id = %s'
    cursor.execute(sql, (user_id,))
    state = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    if state != None:
        return state[0]
    else:
        return States.St_start.value

# Сохраняем текущее «состояние» пользователя в нашу базу
def set_state(user_id, value):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()
    sql = "SELECT state FROM public.user_state WHERE id = %s"
    cursor.execute(sql, (user_id,))
    get_state = cursor.fetchone()
    conn.commit()
    if get_state is None:
        sql = 'INSERT INTO public.user_state VALUES (%s, %s)'
        cursor.execute(sql, (user_id, value))
        conn.commit()
    else:
        sql = 'UPDATE public.user_state SET state = %s WHERE id = %s'
        cursor.execute(sql, (value, user_id))
        conn.commit()
    cursor.close()
    conn.close()
    return True

# импортируем библиотеки и файлы
import config
import telebot
import re
import work_with_db as wdb
import datetime
from vedis import Vedis
from os import remove
from random import randint
from flask import Flask, request
import os

# создаем приложение flask
server = Flask(__name__)


# Создаем бота
bot = telebot.TeleBot(config.token)

# создаем кэш в памяти
cashe = Vedis()
# берем базу данных с котами (нет в репозитории, это база Vedis с id (целочисленное значение) и file_id каждой картинки)
cat_db = Vedis('cat_db.vdb')

# создаем клавиатуру с вариантами ответов
def reply_keabord():
    markup = telebot.types.ReplyKeyboardMarkup()
    spend_today = telebot.types.InlineKeyboardButton(text='/today_spend') # сделано
    help_button = telebot.types.InlineKeyboardButton(text='/help') # сделано
    General_info_button = telebot.types.InlineKeyboardButton(text='/get_general') # сделано
    Top_5_cat_button = telebot.types.InlineKeyboardButton(text='/top5_cat') # сделано
    Last_5_spendings = telebot.types.InlineKeyboardButton(text='/last5_spend') # сделано
    cat_button = telebot.types.InlineKeyboardButton(text='/cat')
    new_month = telebot.types.InlineKeyboardButton(text='/new_month')
    full_table = telebot.types.InlineKeyboardButton(text='/full_table')
    markup.row(spend_today, help_button)
    markup.row(General_info_button, Top_5_cat_button)
    markup.row(Last_5_spendings, cat_button)
    markup.row(new_month, full_table)
    return markup

# Первое состояние - приветствие и предложение ввести основные траты и проверка на состояние
@bot.message_handler(commands=["start"])
def cmd_start(message):
    bot.send_message(message.chat.id, config.greeting, reply_markup=reply_keabord())
    current_state = wdb.get_current_state(message.chat.id)
    # здесь проверяем на состояние 2
    if current_state == config.States.St_enter_spendings.value:
        bot.send_message(message.chat.id, config.continue_input_spendings)
    # здесь проверяем на состояние 1
    elif current_state == config.States.St_enter_general_info.value:
        bot.send_message(message.chat.id, config.change_general_data)
    # здесь обрабатываем состояние 4 - меняние основной инфы
    elif current_state == config.States.St_change_general_info.value:
        bot.send_message(message.chat.id, config.change_general_data)
    elif current_state == config.States.St_new_month.value:
        bot.send_message(message.chat.id, config.new_month)
    elif current_state == config.States.St_ask_for_table.value:
        bot.send_message(message.chat.id, config.ask_for_table_mes)
    # здесь старт - состояние 0
    else:
        bot.send_message(message.chat.id, config.start_message)
        wdb.set_state(message.chat.id, config.States.St_enter_general_info.value)

# Ниже описываем команды:

# команда /new_month
@bot.message_handler(commands=['new_month'])
def new_month(message):
    bot.send_message(message.chat.id, config.new_month)
    wdb.set_state(message.chat.id, config.States.St_new_month.value)

# Здесь состояние new_month - то есть когда пользователь выбрал команду нового месяца и ввел новые данные
@bot.message_handler(
    func=lambda message: wdb.get_current_state(message.chat.id) == config.States.St_new_month.value)
def enter_general_info(message):
    if re.match(config.general_pattern, message.text) is None:
        bot.send_message(message.chat.id, config.wrong_general_data)
    else:
        # считаем нынешнюю дату
        month = datetime.datetime.now().month
        year = datetime.datetime.now().year
        # получаем айди юзера
        user_id = int(message.from_user.id)
        if wdb.get_general_info(user_id, month, year) is None:
            # разбиваем сообщение и вычленяем из него заработок, обязательные траты и сумму для накопления
            input_sums = message.text.split(', ')
            annual_earning = int(input_sums[0])
            annual_spendings = int(input_sums[1])
            plan_to_save = int(input_sums[2])
            # вставляем данные в базу данных
            wdb.insert_general_info(user_id, month, year, annual_earning, annual_spendings, plan_to_save)
            bot.send_message(message.chat.id, config.general_info_inputed)
        else:
            bot.send_message(message.chat.id, 'Кажется, новый месяц еще не наступал. ' + config.insert_spendings_mes)
        # меняем состояние на 2 - предлагаем ввести траты
        wdb.set_state(message.chat.id, config.States.St_enter_spendings.value)


# здесь описываем команду получения основной инфы. в ней можно поменять данные за месяц
@bot.message_handler(commands=['get_general'])
def get_general_info_and_maybe_change(message):
    month = datetime.datetime.now().month
    year = datetime.datetime.now().year
    user_id = message.from_user.id
    # получаем основные даннные
    general_info = wdb.get_general_info(message.from_user.id, month, year)
    # 0 - доход за месяц, 1 - обязательные траты за месяц, 2 - оставшиеся деньги на месяц, 3 -
    # потрачено за месяц, 4 - планируется отложить за месяц
    # разбиваем сообщение для удобства
    if general_info is None:
        bot.send_message(message.chat.id, config.no_general_info)
    else:
        annual_earning = general_info[0]
        annual_spending = general_info[1]
        money_for_spendings = general_info[2]
        spend_for_month = general_info[3]
        planning_to_save = general_info[4]
        left_to_spend = money_for_spendings - spend_for_month
        # создаем клавиатуру, в которой предлагаем поменять траты или оставить все как есть
        keybord = telebot.types.InlineKeyboardMarkup(row_width=2)
        Yes_button = telebot.types.InlineKeyboardButton(text="Да", callback_data="Меняем")
        No_button = telebot.types.InlineKeyboardButton(text="Нет", callback_data="Оставляем")
        keybord.add(Yes_button, No_button)
        # здесь посылаем сообщение с инфой и предложением поменять данные
        bot.send_message(message.chat.id, config.show_general_data.format(annual_earning, annual_spending, planning_to_save,
                                                                      spend_for_month, left_to_spend), reply_markup=keybord)

# делаем обработчик для кнопок из general
@bot.callback_query_handler(func=lambda call: call.data == 'Оставляем' or call.data == 'Меняем')
def change_general_or_leave(call):
    if call.message:
        if call.data == 'Оставляем':
            bot.send_message(call.message.chat.id, 'Ок!')
        if call.data == 'Меняем':
            bot.send_message(call.message.chat.id, config.change_general_data)
            wdb.set_state(call.message.chat.id, config.States.St_change_general_info.value)

# обрабатываем состояние изменения основных трат
@bot.message_handler(func=lambda
        message: wdb.get_current_state(message.chat.id) == config.States.St_change_general_info.value)
def change_general_data(message):
    # разбиваем сообщение и вычленяем из него заработок, обязательные траты и сумму для накопления
    input_sums = message.text.split(', ')
    annual_earning = int(input_sums[0])
    annual_spending = int(input_sums[1])
    plan_to_save = int(input_sums[2])
    month = datetime.datetime.now().month
    year = datetime.datetime.now().year
    user_id = message.from_user.id
    # вставляем новые траты
    wdb.update_general_info(user_id, month, year, annual_earning, annual_spending, plan_to_save)
    bot.send_message(message.chat.id, 'Данные изменены!')
    wdb.set_state(message.chat.id, config.States.St_enter_spendings.value)

# описыываем команду /today_spend - сколько потрачено за день
@bot.message_handler(commands=['today_spend'])
def spend_today(message):
    user_id = message.from_user.id
    month = datetime.datetime.now().month
    year = datetime.datetime.now().year
    day = datetime.datetime.now().day
    today_spend = wdb.today_info(user_id, day, month, year)
    if today_spend is None:
        bot.send_message(message.chat.id, 'Похоже, сегодня вы ничего не потратили. ' + config.insert_spendings_mes)
    else:
        bot.send_message(message.chat.id, wdb.today_info(user_id, day, month, year))

# описываем команду /top5_cat - топ 5 категорий за месяц
@bot.message_handler(commands=['top5_cat'])
def show_top_5_cat(message):
    user_id = message.from_user.id
    month = datetime.datetime.now().month
    year = datetime.datetime.now().year
    categ_info = wdb.top5_cat_answer(user_id, month, year)
    if categ_info is None:
        bot.send_message(message.chat.id, 'Похоже, вы eщe ничего не потратили. ' + config.insert_spendings_mes)
    else:
        bot.send_message(message.chat.id, wdb.top5_cat_answer(user_id, month, year))

# описываем команду /last5_spend - показывает 5 последних трат
@bot.message_handler(commands=['last5_spend'])
def show_last_5_spendings(message):
    user_id = message.from_user.id
    month = datetime.datetime.now().month
    year = datetime.datetime.now().year
    answer = wdb.last5_answer(user_id, month, year)
    if answer is None:
        bot.send_message(message.chat.id, 'Похоже, вы eщe ничего не потратили. ' + config.insert_spendings_mes)
    else:
        bot.send_message(message.chat.id, answer)

# описываем команду /help
@bot.message_handler(commands=["help"])
def help_command(message):
    bot.send_message(message.chat.id, config.help_text, reply_markup=reply_keabord())

# описываем команду /cat
@bot.message_handler(commands=['cat'])
def cat_command(message):
    random_number = randint(1, 112)
    bot.send_photo(message.chat.id, cat_db[str(random_number)].decode('utf-8'))

# описываем команду reset
@bot.message_handler(commands=["reset"])
def cmd_reset(message):
    bot.send_message(message.chat.id, "Заново")
    wdb.set_state(message.chat.id, config.States.St_start.value)

# описываем команду full_table
@bot.message_handler(commands=['full_table'])
def ask_for_table(message):
    bot.send_message(message.chat.id, config.ask_for_table_mes)
    wdb.set_state(message.chat.id, config.States.St_ask_for_table.value)

# здесь описываем состояние запроса таблицы
@bot.message_handler(
    func=lambda message: wdb.get_current_state(message.chat.id) == config.States.St_ask_for_table.value)
def sending_a_table(message):
    # смотрим, правильно ли забиты данные
    if re.match(config.ask_for_table_pattern, message.text) is not None and len(message.text) >= 6 <= 7:
        # разбиваем сообщение на месяц и год
        month_and_year = message.text.split(' ')
        month = int(month_and_year[0])
        year = int(month_and_year[1])
        # создаем файл и сохраняем его имя в переменной file_name
        file_name = wdb.create_full_table(message.from_user.id, month, year)
        if file_name is None:
            bot.send_message(message.chat.id, 'Похоже, вы eщe ничего не потратили. ' + config.insert_spendings_mes)
            wdb.set_state(message.chat.id, config.States.St_enter_spendings.value)
        else:
            file = open(file_name, 'rb')
            bot.send_document(message.chat.id, file, None)
            bot.send_message(message.chat.id, config.table_is_ready)
            # не забываем удалить файл
            remove(file_name)
            wdb.set_state(message.chat.id, config.States.St_enter_spendings.value)
    else:
        bot.send_message(message.chat_id, 'Формат данных неправильный! ' + config.ask_for_table_mes)
        wdb.set_state(message.chat.id, config.States.St_enter_spendings.value)



# Здесь обрабатываем сообщение с основными тратами за месяц
@bot.message_handler(
    func=lambda message: wdb.get_current_state(message.chat.id) == config.States.St_enter_general_info.value)
def enter_general_info(message):
    if re.match(config.general_pattern, message.text) is None:
        bot.send_message(message.chat.id, config.wrong_general_data)
    else:
        # разбиваем сообщение и вычленяем из него заработок, обязательные траты и сумму для накопления
        input_sums = message.text.split(', ')
        annual_earning = int(input_sums[0])
        annual_spendings = int(input_sums[1])
        plan_to_save = int(input_sums[2])
        # считаем нынешнюю дату
        month = datetime.datetime.now().month
        year = datetime.datetime.now().year
        # получаем айди юзера
        user_id = int(message.from_user.id)
        # вставляем данные в базу данных
        wdb.insert_general_info(user_id, month, year, annual_earning, annual_spendings, plan_to_save)
        bot.send_message(message.chat.id, config.general_info_inputed)
        # меняем состояние на 2 - предлагаем ввести траты
        wdb.set_state(message.chat.id, config.States.St_enter_spendings.value)


# засовываем его траты (если состояние правильное)
@bot.message_handler(
    func=lambda message: wdb.get_current_state(message.chat.id) == config.States.St_enter_spendings.value)
def enter_spending(message):
    # проверяем, правильно ли введена трата (первый случай - если нет, мы в таком случае кидаем инфу про
    # то, трата неправильная, и предлагаем повторить, статус не меняем)
    if re.match(config.message_pattern, message.text) is None:
        bot.send_message(message.chat.id, config.wrong_info)
    else:
        # случай, когда трата правильно введена. обращаемся к классу spending и разбиваем строку (подробнее в config)
        cashe[message.chat.id] = message.text
        new_spending = config.spending(message.text)
        # создаем клавиатуру с ДА-НЕТ
        keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
        Yes_button = telebot.types.InlineKeyboardButton(text="Да", callback_data="Да")
        No_button = telebot.types.InlineKeyboardButton(text="Нет", callback_data="Нет")
        keyboard.add(Yes_button, No_button)
        # спрашиваем, чтоит ли ввести сию трату? (да или нет)
        bot.send_message(message.chat.id, config.input_spending.format(new_spending.day, new_spending.month,
                                                                       new_spending.year, new_spending.spending,
                                                                       new_spending.category), reply_markup=keyboard
                         )


# обрабатываем кнопки ДА и НЕТ в сообщении с тратами
@bot.callback_query_handler(func=lambda call: (call.data == 'Да') or (call.data == 'Нет'))
def yes_or_no(call):
    if call.message:
        if call.data == 'Да':
            # забираем данные из кэша
            new_spending = cashe[call.message.chat.id].decode('utf-8')
            # обращаемся к классу spending и разбиваем строку (подробнее в config)
            new_spending = config.spending(new_spending)
            # получаем айди юзера
            user_id = int(call.from_user.id)
            # вставляем данные в базу данных
            wdb.insert_spending(user_id, new_spending.day, new_spending.month, new_spending.year, new_spending.spending,
                                new_spending.category)
            # пишем что данные приняты
            bot.send_message(call.message.chat.id, config.spending_was_inputed)
            # удаляем данные
        if call.data == 'Нет':
            # просим ввести данные снова
            bot.send_message(call.message.chat.id, config.spending_was_aborted)
        # удаляем данные из кэша
        del cashe[call.message.chat.id]



# заставляем наше приложение получать новые сообщения от телеграмма
@server.route('/' + config.token, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

# настраиваем вебхук
@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='http://YOUR_URL.com' + config.token)
    return "!", 200


if __name__ == '__main__':
    server.debug = True
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))

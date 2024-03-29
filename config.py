# Здесь хранятся всякие константы
from enum import Enum

# токен, полученый у ботфазера
token = TOKEN

# заготовки ответов

greeting = 'Привет! Я помогаю анализировать траты (и еще я умею присылать фотографии котов).'

start_message = 'Для начала введи свой суммарный доход за месяц, свои обязательные ' \
           'траты и сколько ты хочешь сберечь. Информация должна быть в виде "XXXX, XXXX, XXXX", ' \
           'где вместо XXXX - числа.'

new_month = 'Наступил новый месяц? Введи свой суммарный доход за месяц, свои обязательные ' \
           'траты и сколько ты хочешь сберечь. Информация должна быть в виде "XXXX, XXXX, XXXX", ' \
           'где вместо XXXX - числа.'

no_general_info = 'Информация о основных тратах еще не была внесена. Введи свой суммарный доход за месяц, свои обязательные ' \
           'траты и сколько ты хочешь сберечь. Информация должна быть в виде "XXXX, XXXX, XXXX", ' \
           'где вместо XXXX - числа.'

change_general_data = 'Введи свой суммарный доход за месяц, свои обязательные ' \
           'траты и сколько ты хочешь сберечь. Информация должна быть в виде "XXXX, XXXX, XXXX", ' \
           'где вместо XXXX - числа.'

input_spending = '{}.{}.{} вы потратили {} на категорию "{}". Принять?'

general_info_inputed = 'Спасибо за предоставленную информацию! Теперь ты можешь вводить траты. Формат ввода доступен по' \
                       'команде /help'


continue_input_spendings = 'Похоже, мы уже знакомы! Ты можешь вводить траты. Формат ввода доступен по' \
                       'команде /help'

insert_spendings_mes = 'Ты можешь вводить траты. Формат ввода доступен по' \
                       'команде /help'

wrong_general_data = 'Я не понимаю! Попробуйте ввести данные в виде "XXXX, XXXX, XXXX", ' \
           'где вместо XXXX - числа'

wrong_info = 'Я не понимаю! Используйте /help, чтобы получить пример сообщение с информацией о трате.'

spending_was_inputed = 'Принято! Продолжай вводить траты.'

spending_was_aborted = 'Ну и ладно.'

ask_for_table_mes = 'Введи месяц и год, за который хочешь получить отчет, в формате "X XXXX" (вместо знаков - числа)'

table_is_ready = 'Отчет готов! Продолжай вводить траты. Формат ввода доступен по' \
                       'команде /help'

show_general_data = """
Ваша основная информация:
заработок за месяц: {} р.
обязательные траты за месяц: {} р.
планируется накопить: {} р.
потрачено за месяц: {} р.
осталось потратить: {} р.
Хотите поменять?
                    
"""

help_text = """
Все очень просто! Вводите трату в формате:
ДД.ММ.ГГГГ CУММА КАТЕГОРИЯ
Вам доступны следующие команды:
/help - помощь
/today_spend - узнать, сколько потрачено за день
/get_general - посмотреть и, при необходимости, изменить основную информацию о себе
/top5_cat - посмотреть топ-5 своих категорий и траты на них
/last5_spend - посмотреть 5 последних своих трат
/cat - коты
/new_month - ввести основную информацию для нового месяца
/full_table - присылает вам таблицу с данными обо всем месяце
"""
# Паттерны для регулярок, которые анализируют траты

date_pattern = r'\d{2}.\d{2}.\d{4}'

general_pattern = r'\d{1,10}, \d{1,10}, \d{1,10}'

sum_pattern = r'\d{1,10}'

message_pattern = r'\d{2}.\d{2}.\d{4} \d{1,10} \w+'

ask_for_table_pattern = r'\d{1,2} \d{1,4}'


class States(Enum):
    St_start = 0
    St_enter_general_info = 1
    St_enter_spendings = 2
    St_confirm_a_spending = 3
    St_change_general_info = 4
    St_new_month = 5
    St_ask_for_table = 6

class spending:
    def __init__(self, string):
        string = string.split(' ', 1)
        category_and_spending = string[1].split(' ', 1)
        self.spending = category_and_spending[0]
        self.category = category_and_spending[1]
        date = string[0].split('.')
        self.day = date[0]
        self.month = date[1]
        self.year = date[2]

    def __str__(self):
        str = 'date: {}.{}.{}, '.format(self.day, self.month, self.year) + 'sum: {}, '.format(self.spending) + \
              'category: {}'.format(self.category)
        return str


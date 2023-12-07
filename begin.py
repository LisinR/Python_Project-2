import telebot
from telebot import types
import sqlite3
from datetime import datetime
from constants import *
from captcha2 import captcha
import schedule
import time
import threading


def find_first_lesson():
    current_date = datetime.now()
    weekday = current_date.weekday()
    days_of_week = [MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY]
    current_day = days_of_week[weekday]
    connect = sqlite3.connect('timetable.db')
    cursor = connect.cursor()
    query = f'''
                SELECT * 
                FROM timetable 
                WHERE day_of_week = ? 
                AND lesson NOT IN (?, ?)
            '''
    cursor.execute(query, (current_day, REST, BREAK))
    result = cursor.fetchall()
    connect.commit()
    cursor.close()
    connect.close()
    new_result = []
    for elem in result:
        if new_result == []:
            new_result.append((elem[1], elem[5]))
        else:
            if elem[1] != new_result[-1][0]:
                new_result.append((elem[1], elem[5]))
    return new_result


def send_message():
    current_time = datetime.now().strftime('%H:%M:%S')
    if current_time.find(':') == 1:
        current_time = '0' + current_time
    current_time = int(current_time[:2]) * 3600 + int(current_time[3:5]) * 60 + int(current_time[6:])
    check = False
    for time in TIME_ARRAY:
        begin = int(time[:2]) * 3600 + int(time[3:5]) * 60
        if begin - current_time <= 15 * 60 + 30 and begin - current_time >= 15 * 60 - 30:
            check = True
    print(check)
    if check:
        connect = sqlite3.connect('file.db')
        cursor = connect.cursor()
        lessons = find_first_lesson()
        print(lessons)
        query = f'''
                SELECT * 
                FROM users
            '''
        cursor.execute(query)
        array_users = cursor.fetchall()
        print(array_users)
        connect.commit()
        cursor.close()
        connect.close()
        array_id = []
        for elem in array_users:
            group = elem[1]
            lesson = ''
            for gr in lessons:
                if gr[0] == group:
                    lesson = gr[1]
                    break
            if len(lesson) > 0:
                array_id.append((elem[0], lesson))
        print(array_id)
        for elem in array_id:
            user_id = elem[0]
            message_text = f'Привет! Через 15 минут начнется ваша первая пара: {elem[1]}'
            bot.send_message(chat_id=user_id, text=message_text)

def run_schedule():
    schedule.every().minute.do(send_message)
    while True:
        schedule.run_pending()
        time.sleep(1)


def mainmain():
    @bot.message_handler(commands=['start'])
    def main(message):
        do_captcha1(message)

    def main1(message):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Начать работу', callback_data='start work'))
        bot.send_message(message.chat.id,
                         f'Привет, {message.from_user.first_name} {message.from_user.last_name}. Начнем работу?',
                         reply_markup=markup)

    @bot.message_handler(commands=['end'])
    def main(message):
        bot.send_message(message.chat.id, '<b>До новых встреч!</b>', parse_mode='html')

    @bot.message_handler(commands=['edit'])
    def main(message):
        do_captcha2(message)

    def main2(message):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Изменить группу', callback_data='edit group'))
        markup.add(types.InlineKeyboardButton('Изменить расписание', callback_data='edit schedule'))
        bot.send_message(message.chat.id, 'Что вы хотите изменить?', reply_markup=markup)

    @bot.callback_query_handler(func=lambda callback: True)
    def callback_message(callback):
        if callback.data == 'start work':
            start_work(callback.message)
        if callback.data == 'continue':
            continue_work(callback.message)
        if callback.data == 'lesson now':
            lesson_now_work(callback.message)
        if callback.data == 'lesson in time':
            lesson_in_time_work_start(callback.message)
        if callback.data == 'lessons today':
            lessons_today_work(callback.message)
        if callback.data == 'lessons on day':
            lessons_tomorrow_work(callback.message)
        if callback.data == 'edit group':
            edit_group_work(callback.message)
        if callback.data == 'edit schedule':
            edit_schedule_work(callback.message)
        if callback.data == 'edit anyway':
            edit_schedule1(callback.message)
        if callback.data == 'check again1':
            do_captcha1(callback.message)
        if callback.data == 'check again2':
            do_captcha2(callback.message)

    def do_captcha1(message):
        bot.send_message(message.chat.id,
                         'Пройдите проверку на то, что вы человек. Напишите, что вы видите на картинке')
        result = captcha(message).lower()
        bot.register_next_step_handler(message, check_answer1, result)

    def check_answer1(message, result):
        answer = message.text.lower().replace(" ", "")
        if answer == result:
            bot.send_message(message.chat.id, 'Поздравляю, проверка пройдена')
            main1(message)
        else:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton('Попробовать еще раз', callback_data=f'check again1'))
            bot.send_message(message.chat.id, 'К сожалению, вы не прошли проверку', reply_markup=markup)

    def do_captcha2(message):
        bot.send_message(message.chat.id,
                         'Пройдите проверку на то, что вы человек. Напишите, что вы видите на картинке')
        result = captcha(message).lower()
        bot.register_next_step_handler(message, check_answer2, result)

    def check_answer2(message, result):
        answer = message.text.lower().replace(" ", "")
        if answer == result:
            bot.send_message(message.chat.id, 'Поздравляю, проверка пройдена')
            main2(message)
        else:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton('Попробовать еще раз', callback_data=f'check again2'))
            bot.send_message(message.chat.id, 'К сожалению, вы не прошли проверку', reply_markup=markup)

    def start_work(message):
        connect = sqlite3.connect('file.db')
        cursor = connect.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS users ('
                       'id INTEGER PRIMARY KEY,'
                       'group_name TEXT,'
                       'username TEXT)')
        connect.commit()
        cursor.close()
        connect.close()
        if user_already_registered(message):
            continue_work(message)
        else:
            bot.send_message(message.chat.id, 'Давайте вас зарегистрируем. Напишите вашу группу.')
            bot.register_next_step_handler(message, user_group)

    def user_already_registered(message):
        connect = sqlite3.connect('file.db')
        user_id = message.chat.id
        cursor = connect.cursor()
        cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
        data = cursor.fetchone()
        cursor.close()
        connect.close()
        return data is not None

    def user_group(message):
        group_name = message.text.strip()
        connect = sqlite3.connect('file.db')
        cursor = connect.cursor()
        cursor.execute('INSERT INTO users (id, group_name, username) VALUES (?, ?, ?)',
                       (message.chat.id, group_name, message.from_user.username))
        connect.commit()
        cursor.close()
        connect.close()
        markup = types.InlineKeyboardMarkup()
        button0 = types.InlineKeyboardButton('Продолжить работу', callback_data='continue')
        markup.add(button0)
        bot.send_message(message.chat.id, 'Пользователь зарегистрирован', reply_markup=markup)

    def continue_work(message):
        markup = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton('Какая сейчас пара?', callback_data='lesson now')
        button2 = types.InlineKeyboardButton('Какие пары проходят сегодня?', callback_data='lessons today')
        button3 = types.InlineKeyboardButton('Какие пары проходят в нужный день недели?',
                                             callback_data='lessons on day')
        button4 = types.InlineKeyboardButton('Узнать, какая будет пара в нужное время', callback_data='lesson in time')
        markup.add(button1)
        markup.add(button2)
        markup.add(button3)
        markup.add(button4)
        bot.send_message(message.chat.id, 'Что вы хотите узнать?', reply_markup=markup)

    def find_group(message):
        connect = sqlite3.connect('file.db')
        cursor = connect.cursor()
        query = '''
                SELECT group_name 
                FROM users 
                WHERE id = ?
            '''
        user_id = message.chat.id
        cursor.execute(query, (user_id,))
        group = cursor.fetchone()[0]
        connect.commit()
        cursor.close()
        connect.close()

        connect = sqlite3.connect('timetable.db')
        cursor = connect.cursor()
        query = '''
                    SELECT group_name 
                    FROM timetable 
                    WHERE group_name = ?
                '''
        cursor.execute(query, (group,))
        group = cursor.fetchone()
        connect.commit()
        cursor.close()
        connect.close()
        return group

    def lesson_now_work(message):
        if find_group(message):
            group_name = find_group(message)[0]
            current_date = datetime.now()
            weekday = current_date.weekday()
            days_of_week = [MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY]
            current_day = days_of_week[weekday]
            current_time = datetime.now().strftime('%H:%M:%S')
            if current_time.find(':') == 1:
                current_time = '0' + current_time
            connection = sqlite3.connect('timetable.db')
            cursor = connection.cursor()
            query = f'''
                    SELECT * 
                    FROM timetable 
                    WHERE group_name = ? 
                    AND day_of_week = ? 
                    AND ? >= start_time
                    AND ? < end_time
                '''
            cursor.execute(query, (group_name, current_day, current_time, current_time))
            markup = types.InlineKeyboardMarkup()
            button0 = types.InlineKeyboardButton('Продолжить работу', callback_data='continue')
            markup.add(button0)
            result = cursor.fetchone()
            connection.commit()
            cursor.close()
            connection.close()
            print(current_time)
            print(result)
            bot.send_message(message.chat.id, result[5], reply_markup=markup)
        else:
            markup = types.InlineKeyboardMarkup()
            button0 = types.InlineKeyboardButton('Продолжить работу', callback_data='continue')
            markup.add(button0)
            bot.send_message(message.chat.id,
                             'Извините, расписания вашей группы еще не сделано. Обратитесь к @Lisin_Rodion',
                             reply_markup=markup)

    def lesson_in_time_work_start(message):
        bot.send_message(message.chat.id, 'Напишите день недели')
        bot.register_next_step_handler(message, day_of_week)

    def day_of_week(message):
        day = message.text.lower().replace(" ", "")
        bot.send_message(message.chat.id, 'Напишите время в формате hh:mm')
        bot.register_next_step_handler(message, time_of_day, day)

    def time_of_day(message, day):
        time = message.text.replace(" ", "") + ':00'
        if time.find(':') == 1:
            time = '0' + time
        if find_group(message):
            group_name = find_group(message)[0]
            connection = sqlite3.connect('timetable.db')
            cursor = connection.cursor()
            query = f'''
                    SELECT * 
                    FROM timetable 
                    WHERE group_name = ? 
                    AND day_of_week = ? 
                    AND ? >= start_time
                    AND ? < end_time
                '''
            cursor.execute(query, (group_name, day, time, time))
            markup = types.InlineKeyboardMarkup()
            button0 = types.InlineKeyboardButton('Продолжить работу', callback_data='continue')
            markup.add(button0)
            result = cursor.fetchone()
            connection.commit()
            cursor.close()
            connection.close()
            print(time)
            print(result)
            bot.send_message(message.chat.id, result[5], reply_markup=markup)
        else:
            markup = types.InlineKeyboardMarkup()
            button0 = types.InlineKeyboardButton('Продолжить работу', callback_data='continue')
            markup.add(button0)
            bot.send_message(message.chat.id,
                             'Извините, расписания вашей группы еще не сделано. Обратитесь к @Lisin_Rodion',
                             reply_markup=markup)

    def lessons_today_work(message):
        current_date = datetime.now()
        weekday = current_date.weekday()
        days_of_week = [MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY]
        current_day = days_of_week[weekday]
        lessons_on_day_work(message, current_day)

    def lessons_on_day_work(message, day):
        if find_group(message):
            group_name = find_group(message)[0]
            connection = sqlite3.connect('timetable.db')
            cursor = connection.cursor()
            query = f'''
                    SELECT * 
                    FROM timetable 
                    WHERE group_name = ? 
                    AND day_of_week = ? 
                    AND lesson NOT IN (?, ?)
                '''
            cursor.execute(query, (group_name, day, REST, BREAK))
            markup = types.InlineKeyboardMarkup()
            button0 = types.InlineKeyboardButton('Продолжить работу', callback_data='continue')
            markup.add(button0)
            result = cursor.fetchall()
            connection.commit()
            cursor.close()
            connection.close()
            print(day)
            print(result)
            if len(result) == 0:
                bot.send_message(message.chat.id, 'Пар в этот день нет', reply_markup=markup)
            else:
                result_end = ''
                end = result.pop(-1)
                for elem in result:
                    result_end += elem[3][:-3] + ' - ' + elem[4][:-3] + ': ' + elem[5] + '\n'
                result_end += end[3][:-3] + ' - ' + end[4][:-3] + ': ' + end[5]
                bot.send_message(message.chat.id, result_end, reply_markup=markup)
        else:
            markup = types.InlineKeyboardMarkup()
            button0 = types.InlineKeyboardButton('Продолжить работу', callback_data='continue')
            markup.add(button0)
            bot.send_message(message.chat.id,
                             'Извините, расписания вашей группы еще не сделано. Обратитесь к @Lisin_Rodion',
                             reply_markup=markup)

    def lessons_tomorrow_work(message):
        if find_group(message):
            bot.send_message(message.chat.id, 'Напишите день недели')
            bot.register_next_step_handler(message, day_of_week_2)
        else:
            markup = types.InlineKeyboardMarkup()
            button0 = types.InlineKeyboardButton('Продолжить работу', callback_data='continue')
            markup.add(button0)
            bot.send_message(message.chat.id,
                             'Извините, расписания вашей группы еще не сделано. Обратитесь к @Lisin_Rodion',
                             reply_markup=markup)

    def day_of_week_2(message):
        day = message.text.lower().replace(" ", "")
        lessons_on_day_work(message, day)

    def edit_group_work(message):
        if user_already_registered(message):
            bot.send_message(message.chat.id, 'Напишите вашу новую группу')
            bot.register_next_step_handler(message, edit_group)
        else:
            bot.send_message(message.chat.id,
                             'К сожалению, вы ещё не зарегистрированы. Давайте сделаем это. Напишите вашу группу')
            bot.register_next_step_handler(message, user_group)

    def edit_group(message):
        group = message.text.replace(" ", "")
        user_id = message.chat.id
        connection = sqlite3.connect('file.db')
        cursor = connection.cursor()
        query = '''
                UPDATE users 
                SET group_name = ? 
                WHERE id = ?
            '''
        cursor.execute(query, (group, user_id))
        connection.commit()
        cursor.close()
        connection.close()
        markup = types.InlineKeyboardMarkup()
        button0 = types.InlineKeyboardButton('Продолжить работу', callback_data='continue')
        markup.add(button0)
        bot.send_message(message.chat.id, 'Группа обновлена', reply_markup=markup)

    def edit_schedule_work(message):
        if find_group(message):
            markup = types.InlineKeyboardMarkup()
            button0 = types.InlineKeyboardButton('Изменить расписание', callback_data='edit anyway')
            button1 = types.InlineKeyboardButton('Выйти', callback_data='continue')
            markup.add(button0)
            markup.add(button1)
            bot.send_message(message.chat.id, 'Внимание! Расписание изменится для всей вашей группы!'
                                              ' Будьте осторожны и меняйте расписание только в том случае, если оно изменилось для всей группы.'
                                              'Вы уверены, что хотите продолжить?', reply_markup=markup)
        else:
            markup = types.InlineKeyboardMarkup()
            button0 = types.InlineKeyboardButton('Продолжить работу', callback_data='continue')
            markup.add(button0)
            bot.send_message(message.chat.id,
                             'Извините, расписания вашей группы еще не сделано. Обратитесь к @Lisin_Rodion',
                             reply_markup=markup)

    def edit_schedule1(message):
        bot.send_message(message.chat.id, 'Введите день недели, когда вы хотите изменить расписание')
        bot.register_next_step_handler(message, edit_schedule2)

    def edit_schedule2(message):
        day = message.text.lower().replace(" ", "")
        bot.send_message(message.chat.id, 'Введите номер пары, расписание которой вы хотите изменить')
        bot.register_next_step_handler(message, edit_schedule3, day)

    def edit_schedule3(message, day):
        number = int(message.text.lower().replace(" ", ""))
        time = TIME_ARRAY[number - 1]
        bot.send_message(message.chat.id, 'Введите название новой пары')
        bot.register_next_step_handler(message, edit_schedule4, day, time)

    def edit_schedule4(message, day, time):
        lesson = message.text.lower().replace(" ", "")
        connection = sqlite3.connect('timetable.db')
        cursor = connection.cursor()
        query = '''
                    UPDATE timetable 
                    SET lesson = ? 
                    WHERE day_of_week = ?
                    AND ? >= start_time
                    AND ? < end_time
                '''
        cursor.execute(query, (lesson, day, time, time))
        connection.commit()
        cursor.close()
        connection.close()
        markup = types.InlineKeyboardMarkup()
        button0 = types.InlineKeyboardButton('Продолжить работу', callback_data='continue')
        markup.add(button0)
        bot.send_message(message.chat.id, 'Расписание обновлено', reply_markup=markup)

if __name__ == "__main__":
    bot = telebot.TeleBot(BOT_TOKEN)
    schedule_thread = threading.Thread(target=run_schedule)
    schedule_thread.start()
    mainmain()
    bot.polling(none_stop=True)



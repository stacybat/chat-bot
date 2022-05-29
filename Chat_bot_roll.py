# Импортируем библиотеки
import re
import numpy as np
import random


def help():
    text = '''\nСписок команд:
            /r - simple
            /s - stress
            +/-N - modifier value
            /N - number of botchs
            N - number of rolls
            where N - is a number
            Commands are separated by spaces'''
    return text

# Функция симпл броска
def simple_dice(num, mod):
    rolls = []
    
    for i in range(num):
        roll = random.randrange(1,11) + mod
        rolls.append('Result (mod = ' + str(mod) + '): ' + str(roll + mod) + '  Roll: ' + str(roll))
    
    return rolls

# Функция переброса 1 при стрессовом броске
def stress_1(rolls_stress_1):
    roll = random.randrange(0,10)
    rolls_stress_1.append(roll)
    result = 1
    mul = 1
    #print(rolls_stress_1, mul)
    if roll == 1:
        stress_1(rolls_stress_1)

    mul = pow(2,(len(rolls_stress_1)-1))
    #print(mul)
    if rolls_stress_1[-1] == 0:
        r = 10
    else:
        r = rolls_stress_1[-1]
    result = r*mul
    
    return result, rolls_stress_1

# Функция ботч броска
def botch_dice(botch_num):
    botch_result = 0
    botch_rolls = []
    for _ in range(botch_num):
        roll = random.randrange(0,10)
        botch_rolls.append(roll)
        if roll == 0:
            botch_result +=1
    
    return botch_result, botch_rolls

# Функция стрессового броска
def stress_dice(num, mod, botch):
    # Объявляем переменную stress_results, которая содержит все результаты стрессового броска
    stress_results = [["" for j in range(3)] for i in range(num)]
    all_results = []  

    # Делаем в цикле стрессовые броски, num - количество брошенных кубов
    for i in range(num):
        rolls = []
        botch_result = 0
        roll = random.randrange(0,10)

        # Определяем есть ли ботчи и взрывы
        if roll == 0:
            botch_result, botch_rolls = botch_dice(botch)
            rolls.append(roll)
        elif roll == 1:
            rolls.append(roll)
            result_stress, rolls = stress_1(rolls)
        else:
            rolls.append(roll)

        # Оформляем результат и добавляем если надо модификатор
        if roll == 0 and botch_result == 0:
            result = roll + mod
            stress_results[i][2] = 'No Botch'
        elif roll == 0 and botch_result == 1:
            result = 0
            stress_results[i][2] = '1 Botch' + ' Botch roll: ' + str(botch_rolls)
        elif roll == 0 and botch_result > 1:
            result = 0
            stress_results[i][2] = str(botch_result) + ' Botchs' + ' Botch rolls: ' + str(botch_rolls)
        elif roll == 1:
            result = result_stress + mod
            stress_results[i][2] = ''
        else:
            result = roll + mod
            stress_results[i][2] = ''
        stress_results[i][0] = 'Result (mod = ' + str(mod) + '): ' + str(result)
        stress_results[i][1] = 'Rolls: ' + str(rolls)
        all_results.append(stress_results[i][0] + '  ' + stress_results[i][1] + '  ' + stress_results[i][2])       
    
    return all_results

# Функция в которой кидается либо стресс куб либо симпл куб

def dice(request):
    request=request.lower()
    print(request)

    # разобьем команду пробелами на части
    command = request.split()
    # Изначально присвоим переменным тип куба значение симпл (r), количество бросаемых кубов 1, количество ботч кубов в случае стрессового броска 1, модификатор 0
    dice_type = 'r'
    dice_num = 1
    dice_botch = 1
    modificator = 0
    # Присвоим переменным значение из введенной команды
    for n in command:
        #comm.append(n)
        #print(type(n))
        if n in ['/s', '/r']:
            dice_type = n
        elif  n.isdigit():
            dice_num = int(n)
        elif n[0] == '/' and str(n[1:]).isdigit():
            dice_botch = int(n[1:])
        elif (n[0] == '+' or n[0] == '-') and str(n[1:]).isdigit():
            modificator = modificator + int(n)
        else:
            continue
    # Запускаем функцию либо симпл броска либо стресс броска     
    if dice_type == 'r':
        result = simple_dice(dice_num, modificator)
    else:
        result = stress_dice(dice_num, modificator, dice_botch)
    
    return result



import telebot

# Укажем token полученный при регистрации бота
bot = telebot.TeleBot("***")

# Начнем обработку. Если пользователь запустил бота, ответим 
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.from_user.id, "Greetings! This is a dice bot for Ars Magica")
  
@bot.message_handler(commands=['help'])
def help_message(message):
    bot.send_message(message.from_user.id, help())




@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    request=message.text
    print(request)
    if request[0:2] == '/s' or request[0:2] == '/r':
        
        bot_answer = dice(request)
        for r in bot_answer:     
            print(r)
            #Отправляем результаты бросков построчно
            bot.send_message(message.from_user.id, r)


    
# Запустим обработку событий бота
bot.infinity_polling(none_stop=True, interval=1)

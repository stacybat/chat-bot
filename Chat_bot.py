# Импортируем библиотеки
import pymorphy2
import re
import sklearn
import numpy as np
import os
import pymysql
import pymysql.cursors
from mysql.connector import Error
connection = pymysql.connect(host='localhost',
                             user='root',
                             password='GfhjkmVfqCREK7250',                             
                             db='chat_bot',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor) 
#print ("connect successful!!")
def execute_query(connection, query):
    mycursor = connection.cursor()
    try:
        mycursor.execute(query)
        
        myresult = mycursor.fetchall()
        connection.commit()
        #print("Query successful")
        #print ("cursor.description: ", mycursor.description) 
        #print() 
        mycursor.close()
        return myresult
    except Error as err:
        print(f"Error: '{err}'")

# Настраиваем язык для библиотеки морфологии
morph = pymorphy2.MorphAnalyzer(lang='ru')

# объявляем массив кодов ответов и ответов
answer_id=[] 
answer = dict()

query_select = 'SELECT id, answer FROM chats_answer'
records = execute_query(connection, query_select)
#print(records)
for row in records:
	    answer[row['id']]=row['answer']
#print(answer)
    
# объявляем массив вопросов
questions=[]
query_select = 'SELECT question, answer_id FROM chats_question'
records = execute_query(connection, query_select)
# посчитаем количество вопросов
transform=0
#print(records)
for row in records:
    
    if row['question']>"":
        if row['answer_id']>0:
            phrases=row['question']
            words=phrases.split(' ')
            phrase=""
            for word in words:
                word = morph.parse(word)[0].normal_form  
                phrase = phrase + word + " "
            if (len(phrase)>0):
                questions.append(phrase.strip())
                answer_id.append(row['answer_id'])
                transform=transform+1

# выведем на экран вопросы, ответы и коды ответов
#print (questions)
#print (answer)
#print (answer_id)

connection.close()

# Векторизируем вопросы в огромную матрицу 
# Перемножив фразы на слова из которых они состоят получим числовые значения

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD

vectorizer_q = TfidfVectorizer()
vectorizer_q.fit(questions)
matrix_big_q = vectorizer_q.transform(questions)
#print ("Размер матрицы: ")
#print (matrix_big_q.shape)

# Трансформируем матрицу вопросов в меньший размер для уменьшения объема данных
# Трансформировать будем в 200 мерное пространство, если вопросов больше 200
# Размерность подбирается индивидуально в зависимости от базы вопросов, которая может содержать 1 млн. или 1к вопросов и 1
# Без трансформации большая матрицу будет приводить к потерям памяти и снижению производительности

if transform>200:
    transform=200

svd_q = TruncatedSVD(n_components=transform)
svd_q.fit(matrix_big_q)

# получим трансформированную матрицу
matrix_small_q = svd_q.transform(matrix_big_q)

#print ("Коэффициент уменьшения матрицы: ")
#print ( svd_q.explained_variance_ratio_.sum())
# Тело программы поиска ответов

from sklearn.neighbors import BallTree
from sklearn.base import BaseEstimator

def softmax(x):
    #создание вероятностного распределения
    proba = np.exp(-x)
    return proba / sum(proba)

class NeighborSampler(BaseEstimator):
    def __init__(self, k=5, temperature=10.0):
        self.k=k
        self.temperature = temperature
    def fit(self, X, y):
        self.tree_ = BallTree(X)
        self.y_ = np.array(y)
    def predict(self, X, random_state=None):
        distances, indices = self.tree_.query(X, return_distance=True, k=self.k)
        result = []
        for distance, index in zip(distances, indices):
            result.append(np.random.choice(index, p=softmax(distance * self.temperature)))
        return self.y_[result]

from sklearn.pipeline import make_pipeline

ns_q = NeighborSampler()

# answer_id - код ответа в массиве, который получается при поиске ближайшего ответа
ns_q.fit(matrix_small_q, answer_id) 
pipe_q = make_pipeline(vectorizer_q, svd_q, ns_q)

# код для проверки работы из консоли
'''
print("Пишите ваш вопрос, слова exit или выход для выхода")

request=""

while request not in ['exit', 'выход']:
    # получим текст от ввода
    request=input()

    # разберем фразу на слова
    words= re.split('\W',request)
    phrase=""
    for word in words:
        word = morph.parse(word)[0].normal_form  # морфируем слово вопроса в нормальную словоформу
    # Нормализуем словоформу каждого слова и соберем обратно фразу
    phrase = phrase + word + " "

    # запустим функцию и получим код ответа
    reply_id    = int(pipe_q.predict([phrase.strip()]))

    # выведем текст ответа
    print (answer[reply_id])

'''

import telebot

telebot.apihelper.ENABLE_MIDDLEWARE = True

# Укажем token полученный при регистрации бота
bot = telebot.TeleBot("5325435356:AAE5qn9Mwlp4uqlgxuwr87kmPpFQd8kBQyU")

# Начнем обработку. Если пользователь запустил бота, ответим 
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.from_user.id, "Heus! Sum in Pitsdim bot")

# Если пользователь что-то написал, ответим
@bot.message_handler(func=lambda message: True)
def get_text_messages(message):
    request=message.text

    # разобьём фразу на массив слов, используя split. '\W' - любой символ кроме буквы и цифры
    words= re.split('\W',request)
    phrase=""

    # разберем фразу на слова, нормализуем каждое и соберем фразу
    for word in words:
        word = morph.parse(word)[0].normal_form  
    phrase = phrase + word + " "

    # получим код ответа вызывая нашу функцию 
    reply_id    = int(pipe_q.predict([phrase.strip()]))

    # отправим ответ
    bot.send_message(message.from_user.id, answer[reply_id])

    # продублируем ответ пользователю с id=99999999
    # bot.send_message(99999999, str(message.from_user.id) + "\n" + str(message.from_user.first_name) + " " + str(message.from_user.last_name) + " " +str(message.from_user.username) + "\n"+ str(request) + "\n"+ str(answer[reply_id]))

    # выведем в консоль вопрос / ответа
    print("Запрос:", request, " \n\tНормализованный: ", phrase, " \n\t\tОтвет :", answer[reply_id])

# Запустим обработку событий бота
bot.infinity_polling(none_stop=True, interval=1)
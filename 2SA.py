import re
import urllib.request
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
plt.style.use('seaborn-white')

import tensorflow as tf
import MeCab
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.datasets import mnist
from sklearn.model_selection import train_test_split


#데이터 불러오기.. 향후 db로 수정예정
news_df = pd.read_csv("./naver_news.csv",encoding='CP949')

#트레인, 테스트 데이터 나누기
train_data, test_data = train_test_split(news_df, test_size = 0.3)


#한글 제외(특수문자, 알파벳 등) 전부 날리기
train_data['Article'] = train_data['Article'].str.replace("[^ㄱ-ㅎㅏ-ㅣ가-힣 ]", "", regex=True)
train_data['Article'].replace('', np.nan, inplace=True)
train_data = train_data.dropna(how='any')
test_data['Article'] = test_data['Article'].str.replace("[^ㄱ-ㅎㅏ-ㅣ가-힣 ]", "", regex=True)
test_data['Article'].replace('', np.nan, inplace=True)
test_data = test_data.dropna(how='any')


#토큰화 및 불용어 제거
#단어들을 분리하고 불용어를 제거함

stopwords = ['의', '가', '이', '은', '들', '는', '좀', '잘', '걍', '과', '도', '를', '으로', '자,' '에', '와', '한', '하다']

mecab = MeCab.Tagger()


X_train = []
for sentence in train_data['Article']:
    X_train.append([word for word in mecab.parse(sentence) if not word in stopwords])

X_test = []
for sentence in test_data['Article']:
    X_test.append([word for word in mecab.parse(sentence) if not word in stopwords])


tokenizer = Tokenizer()
tokenizer.fit_on_texts(X_train)


threshold =3
words_cnt = len(tokenizer.word_index)
rare_cnt = 0
words_freq = 0
rare_freq = 0

for key, value in tokenizer.word_counts.items():
    words_freq = words_freq + value

    if value < threshold:
        rare_cnt += 1
        rare_freq = rare_freq + value

#print("전체 단어 수 : ", words_cnt)
#print("빈도가 {} 이하인 희귀 단어 수 : {}".format(threshold-1, rare_cnt))
#print("희귀 단어 비율 : {}".format((rare_cnt / words_cnt)*100))
#print("희귀 단어 등장 빈도 비율 : {}".format((rare_freq/words_freq)*100))

vocab_size = words_cnt-rare_cnt+2
#print(vocab_size)

tokenizer = Tokenizer(vocab_size, oov_token='OOV')
tokenizer.fit_on_texts(X_train)
X_train = tokenizer.texts_to_sequences(X_train)
X_test = tokenizer.texts_to_sequences(X_test)

y_train = np.array(train_data['Recommand'])
y_test = np.array(test_data['Recommand'])
print(len(X_train))
print(len(y_train))
drop_train = [index for index, sentence in enumerate(X_train) if len(sentence) < 1]

X_train = np.delete(X_train, drop_train, axis=0)
#y_train = np.delete(y_train, drop_train, axis=0)

#패딩
#리뷰의 전반적인 길이를 확인
#모델의 입력을 위해 동일한 길이로 맞춰줌
#print('최대 길이:', max(len(l) for l in X_train))
#print('평균 길이', sum(map(len, X_train))/len(X_train))

#plt.hist([len(s) for s in X_train], bins=50)
#plt.xlabel('Length of Samples')
#plt.ylabel('Number of Samples')
#plt.show()

max_len = 30000
X_train = pad_sequences(X_train, maxlen=max_len)
X_test = pad_sequences(X_test, maxlen=max_len)


#모델 구축 및 학습

#감정 상태 분류 모델을 선언하고 학습
#모델은 일반적인 LSTM 모델을 사용

from tensorflow.keras.layers import Embedding, Dense, LSTM
from tensorflow.keras.models import Sequential

model = Sequential()
model.add(Embedding(vocab_size, 100))
model.add(LSTM(64))
model.add(Dense(1, activation='sigmoid'))

model.compile(optimizer='rmsprop', loss='binary_crossentropy', metrics=['acc'])
model.summary()

history = model.fit(X_train, y_train, epochs=15, batch_size=60, validation_split=0.2)
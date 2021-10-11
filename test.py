import MeCab
m = MeCab.Tagger()
out = m.parse("미캅이 잘 설치되었는지 확인 중입니다.")
print(out)
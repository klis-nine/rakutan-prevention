from urllib import request
# 取得するURL
url = "https://make-it-tsukuba.github.io/alternative-tsukuba-kdb/"
response = request.urlopen(url)
html = response.read().decode('utf-8')

# 取得したHTMLを処理する
print(html)

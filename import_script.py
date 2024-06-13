import pandas as pd
from your_module import add_class

# 正しい列インデックスを使用
# ここでは仮に、列インデックスが 0, 1, 2, 3, 4, 5, 6, 7 だと仮定しています
df = pd.read_csv("kdb.csv", skiprows=3, header=None, usecols=[0, 1, 2, 3, 4, 5, 6, 7])

# A列が空白の行を削除
df.dropna(subset=[0], inplace=True)

# 科目番号の行（ヘッダー）、行内に5項目以上ない行は削除
df = df[df[0] != "科目番号"].dropna(thresh=5)

# 欠損を空文字に置換
df.fillna("", inplace=True)

# 改行前後の空白を削除
df[6] = df[6].apply(lambda s: "\n".join([i.strip() for i in s.strip().splitlines()]))
df[7] = df[7].apply(lambda s: "\n".join([i.strip() for i in s.strip().splitlines()]))

# 各行のデータをadd_classに渡してデータベースに追加
for class_info in df.values.tolist():
    add_class({
        "class_id": class_info[0],
        "class_name": class_info[2],
        "class_time": class_info[3],
        "class_location": class_info[4],
    })

print("授業情報のインポートが完了しました。")

import sqlite3

def add_class(class_info):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO classes (class_id, class_name, class_time, class_location)
        VALUES (?, ?, ?, ?)
    ''', (class_info['class_id'], class_info['class_name'], class_info['class_time'], class_info['class_location']))
    conn.commit()
    conn.close()

def get_class(class_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM classes WHERE class_id = ?', (class_id,))
    class_info = cursor.fetchone()
    conn.close()
    return class_info

def search_classes(keyword):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT class_id, class_name, class_time, class_location FROM classes
        WHERE class_id LIKE ? OR class_name LIKE ?
    ''', ('%' + keyword + '%', '%' + keyword + '%'))
    classes = cursor.fetchall()
    conn.close()
    return [{"class_id": c[0], "class_name": c[1], "class_time": c[2], "class_location": c[3]} for c in classes]

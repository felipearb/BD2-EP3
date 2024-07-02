from flask import Flask, render_template, request
import psycopg2

app = Flask(__name__)

def get_db_connection():
    conn = psycopg2.connect(
        dbname='meu_banco',
        user='seu_usuario',
        password='sua_senha',
        host='localhost'
    )
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    search_query = request.form['search_query']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM usuarios WHERE nome LIKE %s", ('%' + search_query + '%',))
    results = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)

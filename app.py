from flask import Flask, request, jsonify, render_template
import requests
from bs4 import BeautifulSoup
import mysql.connector
import os

app = Flask(__name__)

# Database setup
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "web_scraper")

def init_db():
    conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
    #conn = mysql.connector.connect(host="localhost" , user="root", password="", database="web_scraper")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS sites (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        url VARCHAR(512) UNIQUE,
                        title TEXT,
                        headers TEXT,
                        tables TEXT)''')
    conn.commit()
    conn.close()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/scrape", methods=["POST"])
def scrape():
    url = request.form.get("url")
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.title.string if soup.title else "No Title"
        headers = [h.get_text() for h in soup.find_all(['h1', 'h2'])]
        tables = [str(table) for table in soup.find_all("table")]
        
        conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
        #conn = mysql.connector.connect(host="localhost" , user="root", password="", database="web_scraper")
        
        cursor = conn.cursor()
        cursor.execute("INSERT IGNORE INTO sites (url, title, headers, tables) VALUES (%s, %s, %s, %s)", 
                       (url, title, str(headers), str(tables)))
        conn.commit()
        conn.close()
        
        return jsonify({"title": title, "headers": headers, "tables": len(tables)})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/search", methods=["GET"])
def search():
    title = request.args.get("title")
    conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sites WHERE title LIKE %s", (f"%{title}%",))
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)

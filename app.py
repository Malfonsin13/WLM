from flask import Flask, request, render_template, redirect
import sqlite3
import os

app = Flask(__name__)

# Database setup
db_file = 'pitcher_data.db'

def create_table():
    if not os.path.exists(db_file):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS pitcher_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pitcher_name TEXT,
                date TEXT,
                total_throws INTEGER,
                high_intent_throws INTEGER,
                workload_score INTEGER,
                peak_torque REAL,
                peak_arm_speed REAL,
                pitched_in_game TEXT,
                touched_mound TEXT,
                avg_fb_velo REAL,
                max_fb_velo REAL
            )
        ''')
        conn.commit()
        conn.close()

create_table()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            conn = sqlite3.connect(db_file)
            c = conn.cursor()
            c.execute('''
                INSERT INTO pitcher_data (pitcher_name, date, total_throws, high_intent_throws, workload_score, peak_torque, peak_arm_speed, pitched_in_game, touched_mound, avg_fb_velo, max_fb_velo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                request.form['pitcher_name'],
                request.form['date'],
                request.form['total_throws'],
                request.form['high_intent_throws'],
                request.form['workload_score'],
                request.form['peak_torque'],
                request.form['peak_arm_speed'],
                request.form['pitched_in_game'],
                request.form['touched_mound'],
                request.form['avg_fb_velo'],
                request.form['max_fb_velo']
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            return f"An error occurred: {e}"
        return redirect('/')
    else:
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("SELECT * FROM pitcher_data")
        rows = c.fetchall()
        conn.close()
        return render_template('index.html', rows=rows)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)

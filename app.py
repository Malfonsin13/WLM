from flask import Flask, request, render_template, redirect, flash
import psycopg2  # For PostgreSQL connection
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for flash messages

# PostgreSQL Database setup
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://workloadmanagement_user:4cqXp3D5MtdYUWV91B0f5vDeMeJClOtg@dpg-csd49udds78s73bin41g-a.oregon-postgres.render.com/workloadmanagement')

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def create_table():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS pitcher_data (
            id SERIAL PRIMARY KEY,
            pitcher_name TEXT,
            date TEXT,
            total_throws INTEGER,
            high_intent_throws INTEGER,
            workload_score REAL,
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
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('''
                INSERT INTO pitcher_data (pitcher_name, date, total_throws, high_intent_throws, workload_score, peak_torque, peak_arm_speed, pitched_in_game, touched_mound, avg_fb_velo, max_fb_velo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                request.form['avg_fb_velo'] if request.form['pitched_in_game'] == 'Y' else None,
                request.form['max_fb_velo'] if request.form['pitched_in_game'] == 'Y' else None
            ))
            conn.commit()
            conn.close()
            flash("Data added successfully!")
        except Exception as e:
            return f"An error occurred: {e}"
        return redirect('/')
    else:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM pitcher_data")
        rows = c.fetchall()
        conn.close()

        # Get the unique pitcher names for the dropdown filter
        pitcher_names = [row[1] for row in rows]
        pitcher_names = list(set(pitcher_names))
        pitcher_names.sort()

        return render_template('index.html', rows=rows, pitcher_names=pitcher_names)

@app.route('/filter', methods=['POST'])
def filter_data():
    pitcher_name = request.form.get('filter_pitcher_name')
    conn = get_db_connection()
    c = conn.cursor()
    if pitcher_name == 'All':
        c.execute("SELECT * FROM pitcher_data")
    else:
        c.execute("SELECT * FROM pitcher_data WHERE pitcher_name = %s", (pitcher_name,))
    rows = c.fetchall()
    conn.close()

    # Get the unique pitcher names for the dropdown filter
    pitcher_names = [row[1] for row in rows]
    pitcher_names = list(set(pitcher_names))
    pitcher_names.sort()

    return render_template('index.html', rows=rows, pitcher_names=pitcher_names, selected_pitcher=pitcher_name)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)

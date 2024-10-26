from flask import Flask, request, render_template, redirect, flash, url_for
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
            pitcher_name = request.form['pitcher_name']
            workload_score = float(request.form['workload_score'])

            # Connect to the database
            conn = get_db_connection()
            c = conn.cursor()

            # Calculate the 50th and 75th percentiles
            c.execute('''
                SELECT
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY workload_score) AS p50,
                    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY workload_score) AS p75
                FROM pitcher_data
                WHERE pitcher_name = %s AND workload_score IS NOT NULL
            ''', (pitcher_name,))
            percentiles = c.fetchone()
            p50, p75 = percentiles[0], percentiles[1]

            # Determine the 'Type' based on the new workload_score
            if p50 is None or p75 is None:
                type_value = 'UNKNOWN'
            else:
                if workload_score < p50:
                    type_value = 'LOW'
                elif workload_score < p75:
                    type_value = 'MEDIUM'
                else:
                    type_value = 'HIGH'

            # Now insert the data including the 'type' value
            c.execute('''
                INSERT INTO pitcher_data (
                    pitcher_name, date, total_throws, high_intent_throws, workload_score,
                    peak_torque, peak_arm_speed, pitched_in_game, touched_mound, avg_fb_velo,
                    max_fb_velo, type
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                pitcher_name,
                request.form['date'],
                request.form['total_throws'],
                request.form['high_intent_throws'],
                workload_score,
                request.form['peak_torque'],
                request.form['peak_arm_speed'],
                request.form['pitched_in_game'],
                request.form['touched_mound'],
                request.form['avg_fb_velo'] if request.form['pitched_in_game'] == 'Y' else None,
                request.form['max_fb_velo'] if request.form['pitched_in_game'] == 'Y' else None,
                type_value
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

@app.route('/update_data', methods=['POST'])
def update_data():
    try:
        conn = get_db_connection()
        c = conn.cursor()

        ids = set()
        for key in request.form.keys():
            if '_' in key:
                field_name, row_id = key.rsplit('_', 1)
                ids.add(row_id)
        for row_id in ids:
            pitcher_name = request.form.get(f'pitcher_name_{row_id}')
            date = request.form.get(f'date_{row_id}')
            total_throws = request.form.get(f'total_throws_{row_id}')
            high_intent_throws = request.form.get(f'high_intent_throws_{row_id}')
            workload_score = request.form.get(f'workload_score_{row_id}')
            peak_torque = request.form.get(f'peak_torque_{row_id}')
            peak_arm_speed = request.form.get(f'peak_arm_speed_{row_id}')
            pitched_in_game = request.form.get(f'pitched_in_game_{row_id}')
            touched_mound = request.form.get(f'touched_mound_{row_id}')
            avg_fb_velo = request.form.get(f'avg_fb_velo_{row_id}')
            max_fb_velo = request.form.get(f'max_fb_velo_{row_id}')

            if not pitcher_name:
                flash(f"Pitcher name is required for row {row_id}")
                continue

            if not date:
                flash(f"Date is required for row {row_id}")
                continue

            try:
                total_throws = int(total_throws) if total_throws else None
                high_intent_throws = int(high_intent_throws) if high_intent_throws else None
                workload_score_value = float(workload_score) if workload_score else None
                peak_torque = float(peak_torque) if peak_torque else None
                peak_arm_speed = float(peak_arm_speed) if peak_arm_speed else None
                avg_fb_velo = float(avg_fb_velo) if avg_fb_velo else None
                max_fb_velo = float(max_fb_velo) if max_fb_velo else None
            except ValueError:
                flash(f"Invalid numeric value in row {row_id}")
                continue
                
            # Calculate percentiles
            c.execute('''
                SELECT
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY workload_score) AS p50,
                    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY workload_score) AS p75
                FROM pitcher_data
                WHERE pitcher_name = %s AND workload_score IS NOT NULL
            ''', (pitcher_name,))
            percentiles = c.fetchone()
            p50, p75 = percentiles[0], percentiles[1]

            # Determine the 'Type' based on the workload_score
            if p50 is None or p75 is None or workload_score_value is None:
                type_value = 'UNKNOWN'
            else:
                if workload_score_value < p50:
                    type_value = 'LOW'
                elif workload_score_value < p75:
                    type_value = 'MEDIUM'
                else:
                    type_value = 'HIGH'

            # Update the row in the database
            c.execute('''
                UPDATE pitcher_data
                SET pitcher_name = %s,
                    date = %s,
                    total_throws = %s,
                    high_intent_throws = %s,
                    workload_score = %s,
                    peak_torque = %s,
                    peak_arm_speed = %s,
                    pitched_in_game = %s,
                    touched_mound = %s,
                    avg_fb_velo = %s,
                    max_fb_velo = %s,
                    type = %s
                WHERE id = %s
            ''', (
                pitcher_name,
                date,
                total_throws,
                high_intent_throws,
                workload_score_value,
                peak_torque,
                peak_arm_speed,
                pitched_in_game,
                touched_mound,
                avg_fb_velo,
                max_fb_velo,
                type_value,
                row_id
            ))
        conn.commit()
        conn.close()
        flash("Data updated successfully!")
    except Exception as e:
        return f"An error occurred: {e}"
    return redirect('/')


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)

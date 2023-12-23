from flask import Flask, render_template, request, redirect, session, url_for
import subprocess
import pandas as pd
import plotly.express as px
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import time

app = Flask(__name__)
app.secret_key = 'multilogin@123'

def generate_matplotlib_plot():
    plt.figure()
    plt.plot([1, 2, 3], [4, 5, 6])
    plt.title('Sample Plot')
    plt.xlabel('X-axis')
    plt.ylabel('Y-axis')

    # Save the plot to a file in the static folder
    plot_path = 'static/matplotlib_plot.png'
    plt.savefig(plot_path)
    plt.close()

    return plot_path

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/page2', methods=['GET', 'POST'])
def page2():
    if request.method == 'POST':
        session['username'] = request.form['username']
        session['password'] = request.form['password']
        session['profileid'] = request.form['profileid']
        session['folderid'] = request.form['folderid']
        username = session.get('username')
        password = session.get('password')
        profileid = session.get('profileid')
        folderid = session.get('folderid')
        print("Session values: ", session)

        return render_template('form.html', username=username, password=password, profileid=profileid, folderid=folderid)

    return redirect(url_for('login'))
     

@app.route('/start_script', methods=['POST'])
def start_script():

    try:
        number = int(request.form['number'])
        keywords = request.form['combinedValues']
        username = session.get('username')
        password = session.get('password')
        profileid = session.get('profileid')
        folderid = session.get('folderid')
        
        command = [
            'python3',
            'script.py',
            '--number', str(number),
            '--keywords', keywords,
            '--email', username,
            '--password', password,
            '--profileid', profileid,
            '--folderid', folderid
        ]

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return_code = process.wait()
        output, error = process.communicate()
        print("Output:", output.decode('utf-8'))
        print("Error:", error.decode('utf-8'))
        if return_code == 0:
            print("Script executed successfully.")
        else:
            print("Error executing script.py.")
        time.sleep(1)
        file_path = generate_matplotlib_plot()

        return redirect(url_for('display_df', plot_path=file_path))
    except subprocess.CalledProcessError as e:
            return f"Error executing script.py: {e.output}"

@app.route('/results', methods=['POST','GET'])
def display_df():
    file_path = 'list-output.xlsx'
    df = pd.read_excel(file_path)

    # Create a bar chart
    plt.bar(df['Keyword'], df['Number of companies'])
    plt.title('Number of companies vs keywords')
    plt.xlabel('Keyword')
    plt.ylabel('Number of companies')

    # Save the plot to a file
    plot_filename = 'static/matplotlib_plot.png'
    plt.savefig(plot_filename)

    # Pass the filename to the HTML template
    return render_template('display_df.html', df=df, plot_filename=plot_filename)

if __name__ == '__main__':
    app.run(debug=True)

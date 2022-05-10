from flask import Flask,\
                  render_template,\
                  url_for,\
                  request,\
                  flash,\
                  redirect
import psycopg2

import sql_scripts
from utils import *
from datetime import date

app = Flask(__name__, static_url_path='')
app.config['SECRET_KEY'] = "2b3f12f3ef12a6c86b"




@app.route('/admin/', methods=['GET', 'POST'])
def admin_home():
   substance_list = ['a', 'b', 'c', 'd']
   return render_template("home.html", substances=substance_list)
   # return render_template("test.html")


if __name__ == "__main__":
   app.run(debug=True)


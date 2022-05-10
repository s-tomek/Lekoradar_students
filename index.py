from flask import Flask,\
                  render_template,\
                  url_for,\
                  request,\
                  flash,\
                  redirect

from utils import *
from datetime import date

app = Flask(__name__, static_url_path='')
app.config['SECRET_KEY'] = "2b3f12f3ef12a6c86b"


@app.route('/admin')
def admin_home():
   substance_list = ['a', 'b', 'c', 'd']
   return render_template("home.html", substances=substance_list)
   # return render_template("test.html")

@app.route("/results")
def results():
    # TODO tutaj wstawiam funkcję od Asi, która zwraca tabelę wynikową dla konkretnej substancji aktywnej
    # result_table = get_result_table(request.args.get('sub'))
    result_table = [["h1", "h2", "h3", "h4"], ["a", "b", "c", "d"], ["e", "f", "g", "h"], ["i", "j", "k", "l"]]
    return render_template("results.html", table=result_table, sub=request.args.get('sub'))

if __name__ == "__main__":
   app.run(debug=True)


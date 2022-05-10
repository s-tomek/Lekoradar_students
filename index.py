from flask import Flask,\
                  render_template,\
                  url_for,\
                  request,\
                  flash,\
                  redirect

from get_data import get_substance_table, get_result_table, get_substance_name

app = Flask(__name__, static_url_path='')
app.config['SECRET_KEY'] = "2b3f12f3ef12a6c86b"


@app.route('/admin')
def admin_home():
    # substances = ['a', 'b', 'c', 'd']
    substances = get_substance_table()
    return render_template("home.html", substances=substances)
    # return render_template("test.html")

@app.route("/results")
def results():
    # TODO tutaj wstawiam funkcję od Asi, która zwraca tabelę wynikową dla konkretnej substancji aktywnej
    sub_id = request.args.get('sub')
    result_table = get_result_table(sub_id)
    sub_name = get_substance_name(sub_id)
    # result_table = [["h1", "h2", "h3", "h4"], ["a", "b", "c", "d"], ["e", "f", "g", "h"], ["i", "j", "k", "l"]]
    return render_template("results.html", table=result_table, sub_name=sub_name)

if __name__ == "__main__":
    app.run(debug=True)


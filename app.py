import pandas as pd
from flask import Flask, render_template

app = Flask(__name__)

crags = pd.read_csv('db/crags_Arco_v2.csv', header=0,
                    names=['name', 'lat', 'long', 'vllocationid', 'cragSlug', 'ascents', 'routes'])


@app.route('/')
def root():
    markers = []
    for ind in crags.index:
        marker = {
            'lat': crags.loc[ind, 'lat'],
            'lon': crags.loc[ind, 'long'],
            'popup': 'This is the middle of the map.'
        }
        markers.append(marker)
    return render_template('index.html', markers=markers)


@app.route('/routes')
def routes():
    markers = []
    return render_template('routes.html', markers=markers)


if __name__ == '__main__':
    app.run(host="localhost", port=8080, debug=True)

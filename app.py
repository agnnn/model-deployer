import sys
import os
import shutil
import time
import traceback
from flask import Flask, request, jsonify
import pandas as pd
from sklearn.externals import joblib
from gcstorage import upload_model, delete_model, get_model, load_model, check_modle


model_directory = 'model'
model_file_name = '%s/model.pkl' % model_directory
model_columns_file_name = '%s/model_columns.pkl' % model_directory


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


app = Flask(__name__)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]


@app.route('/predict', methods=['POST'])
def predict():
    predict.counter += 1
    if clf:
        try:
            json_ = request.json
            query = pd.get_dummies(pd.DataFrame(json_))
            query = query.reindex(columns=model_columns, fill_value=0)
            prediction = clf.predict(query).tolist()
            return jsonify({'prediction': prediction})
        except Exception as e:
            return jsonify({'error': str(e), 'trace': traceback.format_exc()})
    else:
        print('train first')
        return 'no model here'


predict.counter = 0


@app.route('/train', methods=['GET'])
def train():
    from sklearn.ensemble import RandomForestClassifier as rf
    # inputs
    training_data = 'data/titanic.csv'
    include = ['Age', 'Sex', 'Embarked', 'Survived']
    dependent_variable = include[-1]

    df = pd.read_csv(training_data)
    df_ = df[include]

    categoricals = []  # going to one-hot encode categorical variables

    for col, col_type in df_.dtypes.iteritems():
        if col_type == 'O':
            categoricals.append(col)
        else:
            # fill NA's with 0 for ints/floats, too generic
            df_[col].fillna(0, inplace=True)

    # get_dummies effectively creates one-hot encoded variables
    df_ohe = pd.get_dummies(df_, columns=categoricals, dummy_na=True)

    x = df_ohe[df_ohe.columns.difference([dependent_variable])]
    y = df_ohe[dependent_variable]

    # capture a list of columns that will be used for prediction
    global model_columns
    model_columns = x.columns.tolist()
    joblib.dump(model_columns, model_columns_file_name)

    global clf
    clf = rf()
    start = time.time()
    clf.fit(x, y)
    print('Trained in %.1f seconds' % (time.time() - start))
    print('Model training score: %s' % clf.score(x, y))

    joblib.dump(clf, model_file_name)

    return 'Success'


@app.route('/wipe', methods=['GET'])
def wipe():
    try:
        shutil.rmtree('model')
        os.makedirs(model_directory)
        return 'Model wiped'

    except Exception as e:
        print(str(e))
        return 'Could not remove and recreate the model directory'


@app.route('/upload', methods=['POST'])
def uploadmodel():
    bucket_name = request.args.get('bucket_name')
    file_name = request.args.get('file_name')
    file_path = request.args.get('file_path')
    return upload_model(bucket_name, file_name, file_path)


@app.route('/get', methods=['GET'])
def getmodels():
    bucket_name = request.args.get('bucket_name')
    return get_model(bucket_name)


@app.route('/delete', methods=['POST'])
def deletemodel():
    bucket_name = request.args.get('bucket_name')
    file_name = request.args.get('file_name')
    file_path = request.args.get('file_path')
    return delete_model(bucket_name, file_name, file_path)


@app.route('/shutdown', methods=['GET'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'


if __name__ == '__main__':
    try:
        port = int(sys.argv[1])
    except Exception as e:
        port = 5000
    print("Checking if model is valid")
    check_modle(os.getenv("GCS_MODEL_BUCKET", default='generic-model'),
                os.getenv("MODEL_NAME", default='model.pkl'))
    print("Loading model to fs")
    clf = load_model(os.getenv("GCS_MODEL_BUCKET", default='generic-model'),
                     os.getenv("MODEL_NAME", default='model.pkl'))
    app.run(host='0.0.0.0', port=port, debug=False)

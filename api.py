import sys
import os
import shutil
import time
import traceback
from flask import Flask, request, jsonify
import pandas as pd
from sklearn.externals import joblib
from google.cloud import storage
from storage import upload_model, delete_model, get_model, download_model


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


def load_model(bucket_name, source_blob_name, destination_file_name):
    if bucket_name:
        try:
            """Download model from GCS bucket."""
            storage_client = storage.Client()
            bucket = storage_client.get_bucket(bucket_name)  # Bucket name
            blob = bucket.blob(source_blob_name)  # Model Name
            model = blob.download_to_filename(
                destination_file_name)  # Destination file name
            print('Blob {} downloaded to {}.'.format(
                source_blob_name, destination_file_name))
            clf = joblib.load(model)
            return clf
        except Exception as e:
            clf = None
            raise FileNotFoundError(
                "Model found in the GCS bucket:" % (source_blob_name, e))
    else:
        print('Sorry, that model bucket does not exist!')
        return 'Enter a valid modle bucket name'


def upload_model(model_name):
    """Creates a new model in GCS."""
    storage_client = storage.Client()
    bucket = storage_client.upload_model(model_name)
    print('Model {} Uploaded'.format(bucket.name))


app = Flask(__name__)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./service_account.json"

# inputs
#training_data = 'data/titanic.csv'
#include = ['Age', 'Sex', 'Embarked', 'Survived']
#dependent_variable = include[-1]


@app.route('/predict', methods=['POST'])
def predict():
    predict.counter += 1
    if clf:
        try:
            json_ = request.json
            query = pd.get_dummies(pd.DataFrame(json_))

            # https://github.com/amirziai/sklearnflask/issues/3
            # Thanks to @lorenzori
            query = query.reindex(columns=model_columns, fill_value=0)

            prediction = list(clf.predict(query))

            return jsonify({'prediction': prediction})
        except Exception as e:

            return jsonify({'error': str(e), 'trace': traceback.format_exc()})
    else:
        print('train first')
        return 'no model here'


predict.counter = 0


@app.route('/train', methods=['GET'])
def train():
    # using random forest as an example
    # can do the training separately and just update the pickles
    from sklearn.ensemble import RandomForestClassifier as rf

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
    model_columns = list(x.columns)
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
    return get_models()


@app.route('/delete', methods=['POST'])
def deletemodel():
    bucket_name = request.args.get('bucket_name')
    file_name = request.args.get('file_name')
    file_path = request.args.get('file_path')
    return delete_model(bucket_name, file_name, file_path)


@app.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'


if __name__ == '__main__':
    try:
        port = int(sys.argv[1])
    except Exception as e:
        port = 80
    clf = load_model(os.getenv("MODEL_DIR", default='model/'))

    app.run(host='0.0.0.0', port=port, debug=True)

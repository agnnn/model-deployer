import os
import glob
from google.cloud import storage
from sklearn.externals import joblib

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]


def get_model(bucket_name):
    """Lists all the blobs in the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    models = []
    blobs = (bucket.list_blobs())

    for blob in blobs:
        models.append(blob.name)
    return models


def check_modle(bucket_name, model_name):
    """Check if its a valid model avialable in GCS bucket"""
    models = get_model(bucket_name)
    if (model_name in models):
        print('{} is a valid model in GCS bucket'.format(model_name))
        return
    else:
        raise SystemExit("Unexpected model {}! Add {} to GCS bucket and try again.".format(
            model_name, model_name))


def load_model(bucket_name, source_model_name):
    """Load model from GCS bucket."""
    if bucket_name:
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(bucket_name)  # Bucket name
        blob = bucket.blob(source_model_name)  # Source Model Name
        model = blob.download_to_filename(
            './models/{}'.format(source_model_name))
        print('Blob {} downloaded to {}.'.format(
            source_model_name, source_model_name))
        model_directory = './models'
    try:
        # Find the newest model file in the directory
        files = [x for x in os.listdir(model_directory) if x.endswith(".pkl")]
        list_of_files = glob.glob('./models/*.pkl')
        newest = max(list_of_files, key=os.path.getctime)
        print("Recently modified Docs", newest)
        model_file_name = '%s' % (newest)
        print("Model File name", model_file_name)
        # TODO: Fix FileNotFoundError when loading pickled modules
        # FileNotFoundError: [Errno 2] No such file or directory: './models\\model.pkl_01.npy'
        # clf = joblib.load(model_file_name)

        clf = (model_file_name)
        return clf

    except Exception as e:
        clf = None
        raise FileNotFoundError(
            "No model found in {} with suffix '.pkl'{}.".format(model_directory, e))
    else:
        print('Sorry, that model bucket does not exist!')
        return 'Enter a valid modle name'


def upload_model(bucket_name, file_name, file_path):
    """Uploads a blob from the root directory."""
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(file_name)
    blob.upload_from_filename(file_path)  # filename to upload from local fs
    print('Blob {} uploaded.'.format(file_name))
    return blob.public_url


def delete_model(bucket_name, file_name, file_path):
    """Deletes a blob from the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(file_name)
    blob.delete()
    print('Blob {} deleted.'.format(file_name))
    return 'Deleted Model'

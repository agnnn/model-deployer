# Model-Deployer
Flask API for scikit learn
A simple Flask application that can serve predictions from a scikit-learn model. Reads a pickled sklearn model into memory from a Google Cloud Storage bucket.

When the Flask app is started it returns predictions through the /predict endpoint. You can also use the /train endpoint to train/retrain the model. Any sklearn model can be used for prediction.

Use /shutdown endpoint to shutdown the server
other API endpoints for GCS storage.

## Requirements
- GKE Cluster -Google Kubernetes Engine
- GCB -Google Cloud Builder
  - Used as a build trigger to build container images when a commit is made and push the builds to Google Container Registery.

## Pre-Requirements
- Add a kubernetes secret for your GCP service account principle using the following command ``` kubectl create secret generic credentials --from-file ./service_account.json```
- Configure Cloud builder to trigger when a commit is made on the git repo.
- Edit model.yaml with the appropriate GCS bucket name and object(file) name where the models are stored. model.yaml is where we define the kubernetes template
- Edit cloudbuild.yaml with appropriate Kubernetes cluster name and region. cloudbuild.yaml file is used as a pipeline job for container builder, kubernetes deployment, etc... similar to jenkins pipeline.

## Steps
- Edit the model.yaml with bucket name and model(file) name.
- Push git commit and wait for 3 mins for the build to complete and deploy the flask application to kubernetes cluster.
- use ```kubectl get services ``` to get the external LoadBalancer IP of our Demo application.
- try different endpoints ```http://<external-ip>/shutdown```

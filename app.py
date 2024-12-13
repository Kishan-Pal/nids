from flask import Flask, request, jsonify
import joblib
import numpy as np
import pandas as pd
import mysql.connector
from dotenv import load_dotenv
import os
from flask_cors import CORS
import ipaddress

# get mysql connection password from .env
load_dotenv()
SQL_CONNECTION_STRING = os.getenv("SQL_CONNECTION_STRING")

# convert all the non numeric data into numeric values
def convert_to_int(input_data):
    for key, value in input_data.items():
        # convert ip addresses into corresponding integers
        if key == 'ip_src' or key == 'ip_dst':
            ip_int = int(ipaddress.ip_address(value))
            input_data[key] = ip_int

        # converting flags into boolean
        if value == 'True' or value == 'true':
            input_data[key] = 1
        elif value == 'False' or value == 'null':
            input_data[key] = 0
        else:
            input_data[key] = 0
    return input_data

# connect to azure sql database
def get_db_connection():
    connection = mysql.connector.connect(
        host='packet-holder.mysql.database.azure.com',
        user='Kishan',
        password=SQL_CONNECTION_STRING,
        database='packetstore'
    )
    return connection


# load the decision tree model
regression_tree_model = joblib.load("simulation_model1.pkl")

# features used for prediction
feature_names = [
    "frame_len",
    "frame_time_delta",
    "frame_time_relative",
    "ip_src",
    "ip_dst",
    "ip_len",
    "ip_ttl",
    "tcp_srcport",
    "tcp_dstport",
    "tcp_len",
    "tcp_flags_syn",
    "tcp_flags_ack",
    "tcp_flags_fin",
    "tcp_flags_rst",
    "tcp_flags_push",
    "tcp_flags_urg"
]


app = Flask(__name__)

# enable CORS for all origins
CORS(app, resources={r"/predict": {"origins": "*"}})

# empty landing page
@app.route('/')
def index():
    return "<center><h1>Flask App deployment on Azure</h1></center>"

# endpoint to predict the output
@app.route('/predict', methods=['POST'])
def predict():
    try:
        input_data = request.get_json()
        original_data = input_data.copy()
        intput_data = convert_to_int(input_data)

        # if no data received
        if not input_data:
            return jsonify({"error": "No input data provided"}), 400

        # generate a list for the input json
        input_values = [input_data.get(feature) for feature in feature_names]
        original_values = [original_data.get(feature) for feature in feature_names]

        # check for missing feature
        if None in input_values:
            missing_features = [feature_names[i] for i, val in enumerate(input_values) if val is None]
            return jsonify({"error": f"Missing features: {', '.join(missing_features)}"}), 400

        # convert into dataframe
        input_array = np.array(input_values).reshape(1, -1)
        input_df = pd.DataFrame(input_array, columns=feature_names)

        # run the model
        prediction = regression_tree_model.predict(input_df)
        prediction = int(prediction[0])
        prediction_string = "suspicious"
        if prediction == 0:
            prediction_string = "normal"

        # connect to the database
        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
            INSERT INTO packet_data (
                frame_len, frame_time_delta, frame_time_relative, ip_src, ip_dst, ip_len, 
                ip_ttl, tcp_srcport, tcp_dstport, tcp_len, tcp_flags_syn, tcp_flags_ack, 
                tcp_flags_fin, tcp_flags_rst, tcp_flags_push, tcp_flags_urg, prediction
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """



        data = tuple(original_values + [prediction])

        # add data into the database
        cursor.execute(query, data)
        connection.commit()

        cursor.close()
        connection.close()


        return jsonify({"prediction": prediction_string}), 200


    except Exception as e:
        return jsonify({"error exception": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False)

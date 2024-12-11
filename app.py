from flask import Flask, request, jsonify
import joblib
import numpy as np
import pandas as pd
import mysql.connector
from dotenv import load_dotenv
import os
from flask_cors import CORS
import ipaddress


load_dotenv()
SQL_CONNECTION_STRING = os.getenv("SQL_CONNECTION_STRING")

def convert_to_int(input_data):
    for key, value in input_data.items():
        if key == 'ip_src' or key == 'ip_dst':
            ip_int = int(ipaddress.ip_address(value))
            input_data[key] = ip_int

        if value == 'True':
            input_data[key] = 1
        elif value == 'False' or value == 'null':
            input_data[key] = 0
    return input_data


def get_db_connection():
    connection = mysql.connector.connect(
        host='packet-holder.mysql.database.azure.com',
        user='Kishan',
        password=SQL_CONNECTION_STRING,
        database='packetstore'
    )
    return connection



abc = joblib.load("simulation_model1.pkl")

# feature_names = [
#     "duration", "protocol_type", "service", "flag", "src_bytes", "dst_bytes", "land",
#     "wrong_fragment", "urgent", "hot", "num_failed_logins", "logged_in", "num_compromised",
#     "root_shell", "su_attempted", "num_root", "num_file_creations", "num_shells",
#     "num_access_files", "num_outbound_cmds", "is_host_login", "is_guest_login",
#     "count", "srv_count", "serror_rate", "srv_serror_rate", "rerror_rate",
#     "srv_rerror_rate", "same_srv_rate", "diff_srv_rate", "srv_diff_host_rate",
#     "dst_host_count", "dst_host_srv_count", "dst_host_same_srv_rate",
#     "dst_host_diff_srv_rate", "dst_host_same_src_port_rate",
#     "dst_host_srv_diff_host_rate", "dst_host_serror_rate",
#     "dst_host_srv_serror_rate", "dst_host_rerror_rate", "dst_host_srv_rerror_rate"
# ]

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

#CORS(app)
CORS(app, resources={r"/predict": {"origins": "*"}})


@app.route('/')
def index():
    return "<center><h1>Flask App deployment on Azure</h1></center>"

@app.route('/predict', methods=['POST'])
def predict():
    try:
        input_data = request.get_json()
        intput_data = convert_to_int(input_data)


        if not input_data:
            return jsonify({"error": "No input data provided"}), 400

        input_values = [input_data.get(feature) for feature in feature_names]
        if None in input_values:
            missing_features = [feature_names[i] for i, val in enumerate(input_values) if val is None]
            return jsonify({"error": f"Missing features: {', '.join(missing_features)}"}), 400
        print(input_values)
        input_array = np.array(input_values).reshape(1, -1)
        input_df = pd.DataFrame(input_array, columns=feature_names)

        prediction = abc.predict(input_df)


        prediction = int(prediction[0])

        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
            INSERT INTO packet_data (
                frame_len, frame_time_delta, frame_time_relative, ip_src, ip_dst, ip_len, 
                ip_ttl, tcp_srcport, tcp_dstport, tcp_len, tcp_flags_syn, tcp_flags_ack, 
                tcp_flags_fin, tcp_flags_rst, tcp_flags_push, tcp_flags_urg, prediction
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """



        data = tuple(input_values + [prediction])


        cursor.execute(query, data)


        connection.commit()


        cursor.close()
        connection.close()


        return jsonify({"prediction": prediction}), 200


    except Exception as e:
        return jsonify({"error exception": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False)

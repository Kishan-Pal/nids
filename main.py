from flask import Flask, request, jsonify
import joblib
import numpy as np
import pandas as pd
import mysql.connector
from dotenv import load_dotenv
import os


load_dotenv()
SQL_CONNECTION_STRING = os.getenv("SQL_CONNECTION_STRING")




def get_db_connection():
    print("connecting")
    connection = mysql.connector.connect(
        host='packet-holder.mysql.database.azure.com',
        user='Kishan',
        password=SQL_CONNECTION_STRING,
        database='packetstore'
    )
    print("connection successful")
    return connection



#abc = joblib.load("C:/Users/kalya/PycharmProjects/pythonProject/regression_tree_modenew.pkl")
abc = joblib.load("regression_tree_modenew.pkl")

feature_names = [
    "duration", "protocol_type", "service", "flag", "src_bytes", "dst_bytes", "land",
    "wrong_fragment", "urgent", "hot", "num_failed_logins", "logged_in", "num_compromised",
    "root_shell", "su_attempted", "num_root", "num_file_creations", "num_shells",
    "num_access_files", "num_outbound_cmds", "is_host_login", "is_guest_login",
    "count", "srv_count", "serror_rate", "srv_serror_rate", "rerror_rate",
    "srv_rerror_rate", "same_srv_rate", "diff_srv_rate", "srv_diff_host_rate",
    "dst_host_count", "dst_host_srv_count", "dst_host_same_srv_rate",
    "dst_host_diff_srv_rate", "dst_host_same_src_port_rate",
    "dst_host_srv_diff_host_rate", "dst_host_serror_rate",
    "dst_host_srv_serror_rate", "dst_host_rerror_rate", "dst_host_srv_rerror_rate"
]

app = Flask(__name__)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        print("hi")

        input_data = request.get_json()


        if not input_data:
            return jsonify({"error": "No input data provided"}), 400


        print("hi2")
        input_values = [input_data.get(feature) for feature in feature_names]
        if None in input_values:
            missing_features = [feature_names[i] for i, val in enumerate(input_values) if val is None]
            return jsonify({"error": f"Missing features: {', '.join(missing_features)}"}), 400

        input_array = np.array(input_values).reshape(1, -1)
        input_df = pd.DataFrame(input_array, columns=feature_names)

        print("hi4")
        prediction = abc.predict(input_df)

        print("hi5")

        prediction = int(prediction[0])

        connection = get_db_connection()
        print("hiii")
        cursor = connection.cursor()
        print("hi3")

        query = """
                INSERT INTO prediction_data (
                    duration, protocol_type, service, flag, src_bytes, dst_bytes, land,
                    wrong_fragment, urgent, hot, num_failed_logins, logged_in, num_compromised,
                    root_shell, su_attempted, num_root, num_file_creations, num_shells,
                    num_access_files, num_outbound_cmds, is_host_login, is_guest_login,
                    count, srv_count, serror_rate, srv_serror_rate, rerror_rate,
                    srv_rerror_rate, same_srv_rate, diff_srv_rate, srv_diff_host_rate,
                    dst_host_count, dst_host_srv_count, dst_host_same_srv_rate,
                    dst_host_diff_srv_rate, dst_host_same_src_port_rate,
                    dst_host_srv_diff_host_rate, dst_host_serror_rate,
                    dst_host_srv_serror_rate, dst_host_rerror_rate, dst_host_srv_rerror_rate,
                    prediction
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                          %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                          %s, %s, %s, %s, %s,%s,%s)
                """


        data = tuple(input_values + [prediction])


        cursor.execute(query, data)


        connection.commit()


        cursor.close()
        connection.close()


        return jsonify({"prediction": prediction}), 200


    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False)

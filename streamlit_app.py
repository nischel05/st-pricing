import pandas as pd
import pickle
import json
import streamlit as st
import random
import os
import json
df = pd.read_csv('grouped_rpm_cleaned.csv')
def catboost_model():
    with open('catboost_pricing.pkl', "rb") as f:
        pcl = pickle.load(f)
    return pcl

#'miles_bin', 'origin_state', 'dest_state', 'vehicle_size'
cat = catboost_model()

def get_miles_bin(miles):
    if (miles > 300 and miles <= 500):
        bin = 0
    elif (miles > 500 and miles <= 650):
        bin = 1
    elif (miles > 650 and miles <= 900):
        bin = 2
    elif (miles > 900 and miles <= 1200):
        bin = 3
    elif (miles > 1200):
        bin = 4
    else:
        bin = "Error"
    return bin

def get_vehicle_rank(veh):
    if veh == "CARGO VAN":
        return 0
    elif veh == "SPRINTER":
        return 1
    elif veh == "CUBE VAN":
        return 2
    elif veh == "STRAIGHT TRUCK":
        return 3
    elif veh == "TRACTOR":
        return 4
    else:
        return "Error"

def predict(vehicle, mileage, origin_state, dest_state):
    miles_bin = get_miles_bin(int(mileage))
    vehicle_rank = get_vehicle_rank(vehicle)
    if (vehicle_rank == 'Error') | (miles_bin == 'Error'):
        return json.dumps({"Recommended Bid Price": 0, "Lower Bound": 0, "Upper Bound": 0})
    try:
        match = df[(df["miles_bin"] == miles_bin) &
                    (df["origin_state"] == origin_state) & 
                   (df["vehicle_rank"] == vehicle_rank)]["rpm median"].values[0]
    except IndexError:
            origin_df = df[df["origin_state"] == origin_state]
            if origin_df.shape[0] > 0:
                miles_df = origin_df[origin_df["miles_bin"] == miles_bin]
                vehicle_df = origin_df[origin_df["vehicle_rank"] == vehicle_rank]
            else:
                x = [miles_bin, origin_state, dest_state, vehicle]
                match = cat.predict(x)
                predicted = int(match * int(mileage))
                lower = int(predicted * 0.80)
                upper = int(predicted * 1.20)
                return json.dumps({"Recommended Bid Price": predicted, "Lower Bound": lower, "Upper Bound": upper})
            if (miles_df.shape[0] == 0) and (vehicle_df.shape[0] == 0):
                x = [miles_bin, origin_state, dest_state, vehicle]
                match = cat.predict(x)
                predicted = int(match * int(mileage))
                lower = int(predicted * 0.80)
                upper = int(predicted * 1.20)
                return json.dumps({"Recommended Bid Price": predicted, "Lower Bound": lower, "Upper Bound": upper})
            elif (miles_df.shape[0] > 0):
                vehicle_rank_matches = miles_df['vehicle_rank'].unique()
                vehicle_rank_match = min(vehicle_rank_matches, key=lambda x: x if x >= vehicle_rank else float('inf'))
                miles_bin_match = miles_bin  
            else:
                miles_bin_matches = vehicle_df['miles_bin'].unique()
                miles_bin_match = min(miles_bin_matches, key=lambda x: x if x >= miles_bin else float('inf'))
                vehicle_rank_match = vehicle_rank
            match = origin_df[(origin_df["miles_bin"] == miles_bin_match) & 
                              (origin_df["vehicle_rank"] == vehicle_rank_match)]["rpm median"].values[0]     
    predicted = int(match * int(mileage))
    lower = int(predicted * 0.80)
    upper = int(predicted * 1.20)
    return json.dumps({"Recommended Bid Price": predicted, "Lower Bound": lower, "Upper Bound": upper})


st.title("CES Pricing Model Simulator - V1")

def model(input_param_1, input_param_2, input_param_3, input_param_4):
    output_param = predict(input_param_1, input_param_2, input_param_3, input_param_4)
    data_dict = json.loads(output_param)
    bid_price = data_dict
    return bid_price

# Read the input parameter values from a CSV file
input_data = pd.read_csv("streamlit_source.csv")

# Function to get random row from DataFrame
def get_random_row(input_data):
    return input_data.sample(n=1).iloc[0]

# Get column names from DataFrame
columns = ['VEHICLE: CARGO VAN, SPRINTER, CUBE VAN, STRAIGHT TRUCK, TRACTOR',
       'DISTANCE: Miles', 'PICKUP STATE: eg - TX, MI',
       'DESTINATION STATE: eg - WI, IL', 'PICKUP CITY: eg - LAREDO, DALLAS',
       'DESTINATION CITY: eg - HOPKINSVILLE, DALLAS',
       'PICKUP DATE: dd-mm-yyyy', 'DELIVERY DATE: dd-mm-yyyy',
       'Enter Your Bid Price']

# Create a dictionary to store widget values
widget_values = {}

# Populate dictionary with random row values
random_row = get_random_row(input_data)
for col in columns:
    widget_values[col] = str(random_row[col])

# Create Random Values button
if st.button('Get New Bid'):
    # Populate dictionary with new random row values
    random_row = get_random_row(input_data)
    for col in columns:
        # Update widget values
        st.session_state[col] = str(random_row[col])

# Create widgets for each column
for col in columns:
    if col not in st.session_state:
        st.session_state[col] = widget_values[col]
    st.text_input(col, value=st.session_state[col], key=col)

# Create Calculate button
if st.button('Run Pricing Model and Submit'):
    # Replace your_function with the name of your function that takes in the 4 values and generates an output
    result = model(st.session_state[columns[0]], st.session_state[columns[1]], st.session_state[columns[2]], st.session_state[columns[3]])
    st.write(result)
    # Create a new DataFrame with the user input values
    user_input_df = pd.DataFrame({
        "VEHICLE: CARGO VAN, SPRINTER, CUBE VAN, STRAIGHT TRUCK, TRACTOR": st.session_state[columns[0]],
        "DISTANCE: Miles": st.session_state[columns[1]],
        "PICKUP STATE: eg - TX, MI": st.session_state[columns[2]],
        "DESTINATION STATE: eg - WI, IL": st.session_state[columns[3]],
        "PICKUP CITY: eg - LAREDO, DALLAS": st.session_state[columns[4]],
        "DESTINATION CITY: eg - HOPKINSVILLE, DALLAS:":st.session_state[columns[5]],
        "PICKUP DATE: dd-mm-yyyy": st.session_state[columns[6]],
        "DELIVERY DATE: dd-mm-yyyy": st.session_state[columns[7]],
        "Enter Your Bid Price": st.session_state[columns[8]],
        "Pricing Model": [result]})
    output_data = pd.read_csv("steamlit_dump.csv")
    result_data = output_data.append(user_input_df, ignore_index=True)
    result_data.to_csv("steamlit_dump.csv", index=False)

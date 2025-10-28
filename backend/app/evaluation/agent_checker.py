

url  = "http://0.0.0.0:8001"

import requests

url = f"{url}/send_anomaly_data"

payload = {
    "data": """{
"precalciner": {
"temperature": 865,
"pressure": -3.4,
"oxygen_level": 3.2,
"co_level": 0.06,
"nox_level": 540,
"fuel_flow": 10.4,
"feed_rate": 298,
"tertiary_air_temp": 742,
"calcination_degree": 90
},
"rotary_kiln": {
"burning_zone_temp": 1460,
"back_end_temp": 1015,
"shell_temp": 290,
"oxygen_level": 2.3,
"nox_level": 930,
"co_level": 0.03,
"kiln_speed": 4.2,
"fuel_rate": 12.6,
"clinker_exit_temp": 1225,
"secondary_air_temp": 835
},
"clinker_cooler": {
"inlet_temp": 1195,
"outlet_temp": 135,
"secondary_air_temp": 775,
"tertiary_air_temp": 845,
"grate_speed": 22,
"undergrate_pressure": 62,
"cooling_air_flow": 2.9,
"bed_height": 680,
"cooler_efficiency": 80
}"""
}

headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print("Status Code:", response.status_code)
print("Response JSON:", response.json())

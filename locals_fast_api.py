from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import requests
import json
from datetime import datetime, time
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

app = FastAPI()

# Global variables to store data and timestamps
stored_data = {
    "cervejarias": None,
    "produtos": None
}

timestamps = {
    "last_update": None,
    "last_modification": None
}

# Function to fetch and parse data from the first API
def fetch_first_api():
    url = "https://brevo.com.br/ss/bs/0001/hsys?ch=76914f2a9b15a60232d7b6006ccaf677&me=W"
    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36',
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        parsed_data = {}
        for item in data:
            cervejaria = item.get("nomeDaCervejaria")
            if cervejaria not in parsed_data:
                parsed_data[cervejaria] = []

            volumes_and_prices = []
            for i in range(6):  # Iterates over indices 0 to 5
                volume_key = f"volume{i}" if i > 0 else "volume"
                preco_key = f"preco{i}" if i > 0 else "preco"
                servico_key = f"servico{i}" if i > 0 else "servico"

                if item.get(volume_key) and item.get(preco_key):
                    volumes_and_prices.append({
                        "Volume": item.get(volume_key),
                        "Serviço": item.get(servico_key),
                        "Preço": item.get(preco_key),
                    })

            parsed_data[cervejaria].append({
                "Nome": item.get("nome"),
                "Estilo": item.get("estilo"),
                "ABV": item.get("abv"),
                "IBU": item.get("ibu"),
                "Volumes e Preços": volumes_and_prices
            })

        return parsed_data
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch first API data")

# Function to fetch and parse data from the second API
def fetch_second_api():
    url = "https://brevo.com.br/ss/bs/0001/mppa?ch=76914f2a9b15a60232d7b6006ccaf677&me=W"
    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36',
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        parsed_data = []
        for item in data:
            valorese = json.loads(item.get("valorese", "[]"))
            positive_values = [v.get("valor") for v in valorese if v.get("valor", 0) > 0]
            valor = positive_values[0] if positive_values else "N/A"
            parsed_data.append({
                "Nome": item.get("nome"),
                "Nome do Grupo": item.get("nomeDoGrupo"),
                "Valor": valor
            })
        return parsed_data
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch second API data")

# Function to update data
def update_data():
    global stored_data, timestamps
    now = datetime.now()
    # Only update data between 16:00 and 23:00
    if time(10, 0) <= now.time() <= time(23, 0):
        new_data_cervejarias = fetch_first_api()
        new_data_produtos = fetch_second_api()

        # Check for modifications
        if new_data_cervejarias != stored_data["cervejarias"] or new_data_produtos != stored_data["produtos"]:
            timestamps["last_modification"] = now

        # Update stored data and timestamps
        stored_data["cervejarias"] = new_data_cervejarias
        stored_data["produtos"] = new_data_produtos
        timestamps["last_update"] = now
        print(f"Data updated at {now}")
    else:
        print(f"No update performed. Current time: {now}")

# Initial data fetch to ensure data on the first execution
try:
    update_data()
except Exception as e:
    print(f"Error during initial data fetch: {e}")

# Scheduler configuration
scheduler = BackgroundScheduler()
scheduler.add_job(update_data, 'interval', minutes=30)
scheduler.start()

# Ensure the scheduler shuts down properly when the app exits
atexit.register(lambda: scheduler.shutdown(wait=False))

# FastAPI routes
@app.get("/api/cervejarias")
def get_cervejarias():
    return JSONResponse(content=stored_data["cervejarias"] or {}, status_code=200)

@app.get("/api/produtos")
def get_produtos():
    return JSONResponse(content=stored_data["produtos"] or {}, status_code=200)

@app.get("/api/last_update")
def get_last_update():
    return {"last_update": timestamps["last_update"]}

@app.get("/api/last_modification")
def get_last_modification():
    return {"last_modification": timestamps["last_modification"]}

# Root route
@app.get("/")
def root():
    return {"message": "Welcome to the Cervejas e Produtos API!"}

# Run the app with Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

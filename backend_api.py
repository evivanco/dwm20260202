from fastapi import FastAPI

app = FastAPI(
    title="Servicio de Entrenamientos",
    description="Microservicio encargado de rutinas y ejercicios"
)

@app.get("/health")
def health():
    return {"status": "OK", "service": "Workouts & Exercises Service"}

@app.get("/workouts")
def get_workouts():
    return {
        "workouts": [
            {"id": 1, "nombre": "Torso / Pierna", "dias_semana": 4, "nivel": "Intermedio"},
            {"id": 2, "nombre": "Upper / Lower", "dias_semana": 4, "nivel": "Avanzado"},
            {"id": 3, "nombre": "Fullbody Acondicionamiento", "dias_semana": 3, "nivel": "Principiante"}
        ]
    }

@app.get("/exercises")
def get_exercises():
    return {
        "exercises": [
            {"id": 201, "ejercicio": "Press Banca Plano", "grupo_muscular": "Pecho"},
            {"id": 202, "ejercicio": "Sentadilla Libre", "grupo_muscular": "Pierna"},
            {"id": 203, "ejercicio": "Dominadas Pronas", "grupo_muscular": "Espalda"}
        ]
    }
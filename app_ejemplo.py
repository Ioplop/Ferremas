from flask import Flask, jsonify, request
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base

# Configuración básica...
# Crear instancia principal de flask. Es decir, le decimos a flask que este es el archivo principal.
app = Flask(__name__)
# Crear una conexión a la base de datos SQLite usando sqlalchemy.
# echo=True hace que SQLAlchemy muestre por consola lo que se ejecuta.
engine = create_engine('sqlite:///mi_db.sqlite', echo=True)
# Esto devuelve una clase Session configurada para funcionar con el engine (la conexion a sqlite) que creamos en la linea anterior.
# Asi, para usar la bbdd, usaremos Session() para obtener una sesion temporal que podemos usar para hacer solicitudes SQL.
# Notese que cada vez que creamos una sesion usano Session(), debemos cerrarla!
Session = sessionmaker(bind=engine)
# Esto crea una clase base para los modelos. Luego, cada clase o modelo, debera heredar de esta clase base.
# Base guarda metadatos que utiliza SQLAlchemy para generar tablas y cosas por el estilo
Base = declarative_base()

# Modelo
# Aquí definimos una clase que representa una estructura o tabla en la base de datos.
# Estas clases deberan ser separadas en archivos aparte en el proyecto real
class Persona(Base):
    __tablename__ = 'personas'
    # Crear tabla con tres columnas
    id = Column(Integer, primary_key=True)
    nombre = Column(String)
    edad = Column(Integer)

Base.metadata.create_all(engine)  # Crea la tabla si no existe

# Rutas
# Cada una representa una URL de llegada y una solicitud REST.

# Solicitud GET, para buscar una listas de personas
@app.route('/personas', methods=['GET'])
def obtener_personas():
    # Primero abrimos una sesion en sqlite con sqlalchemy
    session = Session()
    # Luego obtenemos una lista de todas las personas.
    personas = session.query(Persona).all()
    # Luego creamos una lista (TIPO LISTA, es decir, una lista de python)
    # que contiene todos los datos de cada persona. Cada persona es un diccionario.
    # Es decir, estamos creando una estructura similar a como funciona JSON, que es serializable 
    # (Que python puede interpretar y convertir en una respuesta valida)
    resultado = [{"id": p.id, "nombre": p.nombre, "edad": p.edad} for p in personas]
    # Ya obtuvimos los resultados del query de SQLite, asi que debemos cerrar la sesion
    session.close()
    # Ahora retornamos los resultados en formato de respuesta HTTP JSON valida.
    return jsonify(resultado)

# Solicitud POST, para ingresar una nueva persona.
@app.route('/personas', methods=['POST'])
def agregar_persona():
    # Obtenemos los datos de la peticion post en formato json
    datos = request.get_json()
    # Creamos una nueva persona usando la clase persona definida arriba
    nueva = Persona(nombre=datos['nombre'], edad=datos['edad'])
    # Abrimos una sesion
    session = Session()
    # Agregamos persona a la tabla
    session.add(nueva)
    # Guardamos cambios
    session.commit()
    # Cerramos la sesion
    session.close()
    return jsonify({"mensaje": "Persona agregada correctamente"})


# Esto hace que el servidor flask solo se ejecute cuando corremos este archivo directamente
# Es decir, si importamos el archivo, no se ejecutara.
if __name__ == '__main__':
    app.run(debug=True)

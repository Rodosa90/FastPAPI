import os # libreria del sistema
from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.ext.declarative import declarative_base # para manipoular la BD


fichero = "../datos.sqlite"
# leemos el directorio actual del archivo de BD
directorio = os.path.dirname(os.path.realpath(__file__))


# direccion BD , uniendo las 2 variables anteriores
ruta = f"sqlite:///{os.path.join(directorio,fichero)}"


#creamos el motor 
motor = create_engine(ruta,echo = True)

#creamos la sesion pasandole el motor
sesion = sessionmaker(bind=motor)


#creamos Base para manehjar las tablas de la BD

base = declarative_base()
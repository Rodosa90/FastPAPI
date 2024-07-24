from fastapi import FastAPI, Body, Path , Query, Request , HTTPException, Depends # depends para securizar rutas.
from fastapi.security import HTTPBearer # PARA PROTEGER MIS RUTAS Y LLAMAR AL TOKEN

from mangum import Mangum # para que encapsule la app y se pueda usar en AWS lamda

from fastapi.responses import HTMLResponse , JSONResponse
from fastapi.encoders import jsonable_encoder # pasar el listado a fomato json

from fastapi.security.http import HTTPAuthorizationCredentials
from pydantic import BaseModel,Field # para tener clases y menos parametros en la funcuones
from typing import Optional, List # para tener parametros opcionales , el LIST es para especificar tipos de respuestas se usa -> en la funciones.

from config.base_de_datos import sesion, motor , base # importamos para la BD
from modelos.ventas import Ventas as VentasModelo 


from jwt_config import get_token, valida_token # importamos DE JWT_CONFIG.py
# se crea instancia de fastapi



app = FastAPI()
handler = Mangum(app) #encapsula la API para ser usada en AWS lamda
app.title = 'Aplicación de Ventas'
app.version = '1.0.1'
base.metadata.create_all(bind = motor)

#Borro la lista de  ventas porque ya tengo la BD
'''ventas = [
    {
        "id":1,
        "fecha":"01/01/23",
        "tienda":"Mercadona",
        "importe": 2500 
    },
    {
        "id":2,
        "fecha":"22/01/23",
        "tienda":"DIA",
        "importe": 4500 
    },
    {
        "id":3,
        "fecha":"29/01/23",
        "tienda":"Carrefour",
        "importe": 6500 
    },
    
]'''


#Creamos el modelo
class Usuario(BaseModel):
    email: str
    clave: str

class Ventas(BaseModel):
    #id: int = Field(ge=0,le=20) # validando dato
    id: Optional[int] = None # DEJAMOS EL ID COMO OPCIONAL YA QUE LA BD GENERA AUTOMATICAMENTE Y COMENTAMOS EL DE ARRIBA.
    fecha: str
    #tienda: str
    #tienda: str =  Field(default="Mercadona",min_length = 4, max_length=10)
    tienda: str =  Field(min_length = 4, max_length=10) # validando dato
    importe: float
    
    class Config: # para poner un ejemplo a nivel de documentación
        json_schema_extra = {
            "example":{
                "id":8,
                "fecha":"01/06/24",
                "tienda":"Tienda01",
                "importe":189.0
            }
        }

# poRTADOR TOKEN la hace asincrona por si tarda mas en la respuesta
class Portador(HTTPBearer):
    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        autorizacion = await super().__call__(request)
        dato = valida_token(autorizacion.credentials)
        if dato['email'] != 'rodolfo@gmail.com':
            raise HTTPException(status_code=403, detail='NO AUTORIZADO')
        
# se crea punto de entra o endpoint

@app.get('/',tags=['Inicio']) #Cambio de etiqueta en documentación
def get_mensaje():
    return HTMLResponse('<h2>Este es mi proyecto con FASTAPI</h2>')


#rUTA PROTEGIDA APARECE EL CANDADO EN MI ENDPOINT EN LA DOCUMENTACION
@app.get('/ventas',tags=['Ventas'],response_model= List[Ventas], status_code= 200, dependencies=[Depends(Portador())]) #el response aqui es lo que vamos a devolver
def get_ventas() -> List[Ventas]:
    db = sesion()
    resultado = db.query(VentasModelo).all()
    return JSONResponse(status_code=200,content=jsonable_encoder(resultado))



@app.get('/ventas/{id}',tags=['Ventas'],response_model= Ventas, status_code= 200,dependencies=[Depends(Portador())])
def get_ventas(id:int = Path(ge = 1,le = 1000)) -> Ventas:
    db = sesion()
    resultado = db.query(VentasModelo).filter(VentasModelo.id ==  id).first()
    if not resultado:
        return JSONResponse(status_code=404, content={'Mensaje':'NO SE ENCONTRO IDENTIFICADOR'})
    '''for elem in ventas:
        if elem['id'] == id:
            return JSONResponse(content=elem, status_code= 200) '''
    return JSONResponse(status_code= 200, content=jsonable_encoder(resultado))



@app.get('/ventas/',tags=['Ventas'] ,response_model=List[Ventas], status_code= 200,dependencies=[Depends(Portador())])
def get_ventas_por_tienda(tienda:str = Query(min_length=4,max_length=20))-> List[Ventas]: # para mas parametros poner  "," id:int
    #return tienda
    db = sesion()
    resultado = db.query(VentasModelo).filter(VentasModelo.tienda ==  tienda).all()
    if not resultado:
        return JSONResponse(status_code=404, content={'Mensaje':'NO SE ENCONTRO ESA TIENDA'})
    return JSONResponse(content= jsonable_encoder(resultado))
    #datos = [ elem for elem in ventas if elem['tienda']== tienda] #antes de la BD
    #return JSONResponse(content=datos) #antes de la BD




@app.post('/ventas',tags=['Ventas'],response_model=dict, status_code= 201,dependencies=[Depends(Portador())])
#def post_venta(id:int = Body(),fecha:str=Body(),tienda:str=Body(),importe:float = Body()): asi era antes de hacer la CLASE
def post_venta(venta:Ventas) -> dict:
    db = sesion() # abrimos una sesion
    #extraemos atributos para paso de parametros
    nueva_venta = VentasModelo(**venta.dict())
    # añadir a BD y hacemos commit para actualizar datos
    db.add(nueva_venta)
    db.commit() 
    #return tienda
    #venta = dict(venta) # convertimos a un dict la venta , se quito al poner la BD
    #ventas.append(venta) , se quito al poner la BD
    #return ventas
    return JSONResponse(content={'Mensaje':'VENTA REGISTRADA EXITOSAMENTE'},status_code= 200)
'''ventas.append(
        {
            "id":id,
            "fecha":fecha,
            "tienda":tienda,
            "importe":importe
        }
) '''
    
    
    
@app.put('/ventas/{id}',tags=['Ventas'],response_model=dict,status_code= 200,dependencies=[Depends(Portador())])
#def update_venta(id:int,fecha:str=Body(),tienda:str=Body(),importe:float = Body()):
def update_venta(id:int,venta:Ventas) -> dict:
    db = sesion() # abrimos una sesion
    resultado = db.query(VentasModelo).filter(VentasModelo.id == id).first()
    if not resultado:
        return JSONResponse(status_code=404, content={'Mensaje':'NO SE HA PODIDO ACTUALIZAR'})
    resultado.fecha = venta.fecha
    resultado.tienda = venta.tienda
    resultado.importe = venta.importe
    db.commit()
    
    #recorre los elementos de la lista
    '''for elem in ventas:
        if elem['id'] == id:
            elem['fecha'] =  venta.fecha
            elem['tienda'] =  venta.tienda
            elem['importe'] = venta.importe'''
    #return ventas
    return JSONResponse(content={'Mensaje':'VENTA ACTUALIZADA EXITOSAMENTE'},status_code= 201)




@app.delete('/ventas/{id}',tags=['Ventas'],response_model=dict,status_code= 200,dependencies=[Depends(Portador())])
def delete_venta(id:int) -> dict:
    db = sesion() # abrimos una sesion
    resultado = db.query(VentasModelo).filter(VentasModelo.id == id).first()
    if not resultado:
        return JSONResponse(status_code=404, content={'Mensaje':'NO SE PUDO BORRAR EL REGISTRO'})
    db.delete(resultado)
    db.commit()
    #recorre los elementos de la lista
    '''for elem in ventas:
        if elem['id'] == id:
            ventas.remove(elem)
    #return ventas'''
    return JSONResponse(content={'Mensaje': 'VENTA BORRADA EXITOSAMENTE'},status_code= 200)


# creamos ruta para login

@app.post('/login',tags=['autenticacion'])
def login(usuario:Usuario):
    if usuario.email == 'rodolfo@gmail.com' and usuario.clave == '1234':
        #obtenemos el token con la función pasandole el diccionario de usuario
        token:str = get_token(usuario.dict())
        return JSONResponse(status_code=200,content={'access_token':token})
    else:
        return JSONResponse(content={'mensaje':'ACCESO DENEGADO'},status_code=403)



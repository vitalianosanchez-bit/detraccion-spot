"""Datos iniciales: tipos de operacion y bienes/servicios para una empresa."""
from models import db, TipoOperacion, BienServicio

TIPO_OPS_DEFAULT = [
    ("01","Venta de bienes o prestacion de servicios"),
    ("02","Retiro de bienes gravados con IGV"),
    ("03","Traslados que no son ventas"),
    ("04","Venta a traves de Bolsa de Productos"),
    ("05","Venta de bienes exonerada del IGV"),
    ("09","Pago Ley N 30737"),
]

BIENES_SERV_DEFAULT = [
    ("001","Azucar y melaza de cana",10,1),
    ("003","Alcohol etilico",10,1),
    ("015","Minerales de oro y sus concentrados gravados con el IGV",10,1),
    ("016","Minerales metalicos no auriferos",10,1),
    ("004","Recursos hidrobiologicos",4,2),
    ("005","Maiz amarillo duro",4,2),
    ("039","Cana de azucar",10,2),
    ("006","Arena y piedra",10,2),
    ("007","Residuos, subproductos, desechos y desperdicios",15,2),
    ("010","Bienes gravados con el IGV por renuncia a la exoneracion",10,2),
    ("040","Carnes y despojos comestibles",4,2),
    ("011","Aceite de pescado",10,2),
    ("012","Harina, polvo y pellets de pescado y crustaceos",4,2),
    ("014","Leche",4,2),
    ("008","Madera",4,2),
    ("041","Oro gravado con el IGV",10,2),
    ("042","Paprika y otros frutos de los generos capsicum o pimienta",10,2),
    ("043","Bienes exonerados del IGV",1.5,2),
    ("044","Oro y demas minerales metalicos exonerados del IGV",1.5,2),
    ("017","Minerales no metalicos",10,2),
    ("045","Plomo",15,2),
    ("029","Intermediacion laboral y tercerizacion",12,3),
    ("019","Arrendamiento de bienes",10,3),
    ("020","Mantenimiento y reparacion de bienes muebles",12,3),
    ("021","Movimiento de carga",10,3),
    ("022","Otros servicios empresariales",12,3),
    ("024","Comision mercantil",10,3),
    ("025","Fabricacion de bienes por encargo",10,3),
    ("026","Servicio de transporte de personas",10,3),
    ("023","Servicio de transporte de carga",4,3),
    ("027","Contratos de construccion",4,3),
    ("028","Demas servicios gravados con el IGV",12,3),
    ("037","Actividades de impresion",12,3),
    ("046","Servicio de beneficio de minerales metalicos gravado con el IGV",12,3),
]

def seed_empresa(empresa_id):
    for cod, desc in TIPO_OPS_DEFAULT:
        if not TipoOperacion.query.filter_by(empresa_id=empresa_id, cod=cod).first():
            db.session.add(TipoOperacion(empresa_id=empresa_id, cod=cod, descripcion=desc, validado=True))
    for cod, desc, pct, anx in BIENES_SERV_DEFAULT:
        if not BienServicio.query.filter_by(empresa_id=empresa_id, cod=cod).first():
            db.session.add(BienServicio(empresa_id=empresa_id, cod=cod, descripcion=desc, pct=pct, anexo=anx, validado=True))
    db.session.commit()

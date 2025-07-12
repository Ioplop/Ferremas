from . import db

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    precio = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    imagen = db.Column(db.String(255))

class Cotizacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, nullable=False)
    productos = db.relationship("CotizacionProducto", back_populates="cotizacion", cascade="all, delete-orphan")

class CotizacionProducto(db.Model):
    __tablename__ = 'producto_cotizacion'
    cotizacion_id = db.Column(
        db.Integer, 
        db.ForeignKey('cotizacion.id', ondelete="CASCADE"), 
        primary_key=True
    )
    producto_id = db.Column(
        db.Integer, 
        db.ForeignKey('producto.id', ondelete="CASCADE"), 
        primary_key=True
    )
    
    cantidad = db.Column(db.Integer, nullable=False)

    producto = db.relationship("Producto", passive_deletes=False)
    cotizacion = db.relationship("Cotizacion", back_populates="productos")

class OrdenCompra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cotizacion_id = db.Column(db.Integer, db.ForeignKey('cotizacion.id'), nullable=False, unique=True)
    
    fecha_envio = db.Column(db.DateTime)
    direccion_entrega = db.Column(db.String(200))
    estado = db.Column(db.String(50), default='pendiente')

    cotizacion = db.relationship("Cotizacion", back_populates="orden_compra")
    
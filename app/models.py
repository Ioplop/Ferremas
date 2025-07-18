from . import db

class Producto(db.Model):
    __tablename__ = 'producto'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    precio = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    reservados = db.Column(db.Integer, default=0)
    imagen = db.Column(db.String(255))

class Cotizacion(db.Model):
    __tablename__ = 'cotizacion'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False)
    fecha = db.Column(db.DateTime, nullable=False)
    bloqueado = db.Column(db.Boolean, default=False)
    total = db.Column(db.Integer, default=0)
    productos = db.relationship("CotizacionProducto", back_populates="cotizacion", cascade="all, delete-orphan")
    orden_compra = db.relationship("OrdenCompra", back_populates="cotizacion", uselist=False)

class CotizacionProducto(db.Model):
    __tablename__ = 'cotizacion_producto'
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
    precio_unidad = db.Column(db.Integer, nullable=False)

    producto = db.relationship("Producto", passive_deletes=False)
    cotizacion = db.relationship("Cotizacion", back_populates="productos")

class OrdenCompra(db.Model):
    __tablename__ = 'orden_compra'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False)

    cotizacion_id = db.Column(
        db.Integer, 
        db.ForeignKey('cotizacion.id'), 
        nullable=False, 
        unique=True
    )

    fecha_envio = db.Column(db.DateTime)
    direccion_entrega = db.Column(db.String(200), nullable=False)
    contacto_nombre = db.Column(db.String(100), nullable=False)
    contacto_email = db.Column(db.String(120), nullable=False)
    contacto_telefono = db.Column(db.String(20), nullable=False)

    metodo_envio = db.Column(db.String(50))  # ej: "retiro", "despacho", etc.
    metodo_pago = db.Column(db.String(50))   # ej: "webpay", "efectivo", etc.

    transaccion = db.Column(db.String(64)) # Token de transaccion transbank
    url = db.Column(db.String(256)) # URL para realizar pago con transbank

    estado = db.Column(db.String(50), default='pendiente')  # pendiente, pagando, pagado, enviando, recibido

    cotizacion = db.relationship("Cotizacion", back_populates="orden_compra")

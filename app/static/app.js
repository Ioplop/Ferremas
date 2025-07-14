const API_BASE = '/api';
let cotizacionUUID = null;

// ------------------- INICIAL -------------------
window.onload = function () {
  crearCotizacion();
  mostrarVista('portada');
  document.getElementById('form-nuevo-producto').addEventListener('submit', crearProducto);
  document.getElementById('bloquearCotizacionBtn').addEventListener('click', bloquearCotizacion);
};

function mostrarVista(vista) {
  var secciones = document.getElementsByClassName('vista');
  for (var i = 0; i < secciones.length; i++) {
    secciones[i].style.display = 'none';
  }
  document.getElementById(vista).style.display = 'block';

  if (vista === 'productos') cargarProductos();
  if (vista === 'carrito') cargarCotizacion();
}

// ------------------- COTIZACIÓN -------------------
function crearCotizacion() {
  var xhr = new XMLHttpRequest();
  xhr.open('POST', API_BASE + '/cotizaciones/', true);
  xhr.onload = function () {
    if (xhr.status === 201) {
      var data = JSON.parse(xhr.responseText);
      cotizacionUUID = data.cotizacion_uuid;
    }
  };
  xhr.send();
}

function bloquearCotizacion() {
  var form = new FormData();
  form.append('uuid', cotizacionUUID);

  var xhr = new XMLHttpRequest();
  xhr.open('PATCH', API_BASE + '/cotizaciones/bloquear', true);
  xhr.onload = function () {
    alert(JSON.parse(xhr.responseText).mensaje);
  };
  xhr.send(form);
}

function cargarCotizacion() {
  var xhr = new XMLHttpRequest();
  xhr.open('GET', API_BASE + '/cotizaciones/?uuid=' + cotizacionUUID, true);
  xhr.onload = function () {
    if (xhr.status === 200) {
      var data = JSON.parse(xhr.responseText)[0];
      var div = document.getElementById('cotizacion');
      div.innerHTML = '';
      for (var i = 0; i < data.productos.length; i++) {
        var p = data.productos[i];
        var item = document.createElement('div');
        item.innerHTML = p.nombre + ' - ' + p.cantidad + ' x $' + p.precio_unidad + ' = $' + p.subtotal;
        div.appendChild(item);
      }
    }
  };
  xhr.send();
}

// ------------------- PRODUCTOS -------------------
function cargarProductos() {
  var xhr = new XMLHttpRequest();
  xhr.open('GET', API_BASE + '/productos/', true);
  xhr.onload = function () {
    if (xhr.status === 200) {
      var productos = JSON.parse(xhr.responseText);
      var contenedor = document.getElementById('lista-productos');
      contenedor.innerHTML = '';
      for (var i = 0; i < productos.length; i++) {
        var producto = productos[i];
        var div = document.createElement('div');
        div.className = 'producto';
        div.innerHTML =
          '<img src="' + producto.imagen + '" width="100">' +
          '<h4>' + producto.nombre + '</h4>' +
          '<p>' + producto.descripcion + '</p>' +
          '<p><strong>$' + producto.precio + '</strong></p>' +
          '<input type="number" min="1" value="1" id="cantidad-' + producto.id + '">' +
          '<button onclick="agregarProducto(' + producto.id + ')">Agregar</button>';
        contenedor.appendChild(div);
      }
    }
  };
  xhr.send();
}

function agregarProducto(productoId) {
  var cantidad = document.getElementById('cantidad-' + productoId).value;
  var form = new FormData();
  form.append('uuid', cotizacionUUID);
  form.append('producto_id', productoId);
  form.append('cantidad', cantidad);

  var xhr = new XMLHttpRequest();
  xhr.open('PATCH', API_BASE + '/cotizaciones/producto', true);
  xhr.onload = function () {
    cargarCotizacion();
  };
  xhr.send(form);
}

// ------------------- ADMIN -------------------
function crearProducto(event) {
  event.preventDefault();

  var apiKey = document.getElementById('api_key').value;
  var nombre = document.getElementById('nombre').value;
  var descripcion = document.getElementById('descripcion').value;
  var precio = document.getElementById('precio').value;
  var stock = document.getElementById('stock').value;
  var imagen = document.getElementById('imagen').files[0];

  var form = new FormData();
  form.append('api_key', apiKey);
  form.append('nombre', nombre);
  form.append('descripcion', descripcion);
  form.append('precio', precio);
  form.append('stock', stock);
  form.append('imagen', imagen);

  var xhr = new XMLHttpRequest();
  xhr.open('POST', API_BASE + '/productos/', true);
  xhr.onload = function () {
    var mensaje = document.getElementById('mensaje-admin');
    if (xhr.status === 201) {
      mensaje.innerText = 'Producto creado con éxito ✅';
      document.getElementById('form-nuevo-producto').reset();
    } else {
      var respuesta = JSON.parse(xhr.responseText);
      mensaje.innerText = 'Error: ' + (respuesta.error || 'no se pudo crear');
    }
  };
  xhr.send(form);
}

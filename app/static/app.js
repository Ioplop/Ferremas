const API_BASE = '/api';
let cotizacionUUID = null;

window.onload = function () {
  mostrarVista('portada');
  document.getElementById('form-nuevo-producto').addEventListener('submit', crearProducto);
  document.getElementById('form-orden-compra').addEventListener('submit', function (e) {
    e.preventDefault();
    crearOrdenDeCompra();
  });
};

function mostrarVista(vista) {
  document.querySelectorAll('.vista').forEach(v => v.style.display = 'none');
  document.getElementById(vista).style.display = 'block';

  if (vista === 'productos') cargarProductos();
  if (vista === 'carrito') cargarCotizacion();
}

function crearCotizacion() {
  return fetch(API_BASE + '/cotizaciones/', {
    method: 'POST'
  })
    .then(res => {
      if (!res.ok) throw new Error("Error al crear cotización");
      return res.json();
    })
    .then(data => {
      cotizacionUUID = data.cotizacion_uuid;
    });
}

function bloquearCotizacion() {
  const form = new FormData();
  form.append('uuid', cotizacionUUID);
  return fetch(API_BASE + '/cotizaciones/bloquear', {
    method: 'PATCH',
    body: form
  });
}

function cargarProductos() {
  fetch(API_BASE + '/productos/')
    .then(res => res.json())
    .then(productos => {
      const contenedor = document.getElementById('lista-productos');
      contenedor.innerHTML = '';
      productos.forEach(p => {
        const div = document.createElement('div');
        div.className = 'producto';
        div.innerHTML = `
          <img src="${p.imagen}" width="100">
          <h4>${p.nombre}</h4>
          <p>${p.descripcion}</p>
          <p><strong>$${p.precio}</strong></p>
          <input type="number" min="1" value="1" id="cantidad-${p.id}">
          <button onclick="pagarProducto(${p.id})">Pagar</button>
        `;
        contenedor.appendChild(div);
      });
    });
}

function pagarProducto(productoId) {
  const cantidad = document.getElementById(`cantidad-${productoId}`).value;

  function continuarFlujo() {
    agregarProducto(productoId, cantidad)
      .then(() => bloquearCotizacion())
      .then(() => {
        mostrarVista('carrito');
        setTimeout(() => document.getElementById('nombre_contacto').focus(), 100);
      })
      .catch(err => {
        console.error(err);
        alert("❌ Error en el proceso de pago");
      });
  }

  if (!cotizacionUUID) {
    crearCotizacion().then(() => continuarFlujo());
  } else {
    continuarFlujo();
  }
}

function agregarProducto(productoId, cantidad) {
  const form = new FormData();
  form.append('uuid', cotizacionUUID);
  form.append('producto_id', productoId);
  form.append('cantidad', cantidad);

  return fetch(API_BASE + '/cotizaciones/producto', {
    method: 'PATCH',
    body: form
  }).then(res => {
    if (!res.ok) throw new Error("Error al agregar producto");
  });
}

function cargarCotizacion() {
  fetch(`${API_BASE}/cotizaciones/?uuid=${cotizacionUUID}`)
    .then(res => res.json())
    .then(data => {
      const cotizacion = data[0];
      const div = document.getElementById('cotizacion');
      div.innerHTML = '';
      cotizacion.productos.forEach(p => {
        const item = document.createElement('div');
        item.innerText = `${p.nombre} - ${p.cantidad} x $${p.precio_unidad} = $${p.subtotal}`;
        div.appendChild(item);
      });
    });
}

function crearOrdenDeCompra() {
  const payload = {
    cotizacion_uuid: cotizacionUUID,
    contacto_nombre: document.getElementById('nombre_contacto').value,
    contacto_email: document.getElementById('email_contacto').value,
    contacto_telefono: document.getElementById('telefono_contacto').value,
    direccion_entrega: document.getElementById('direccion_entrega').value,
    metodo_envio: document.getElementById('metodo_envio').value,
    metodo_pago: document.getElementById('metodo_pago').value
  };

  fetch(API_BASE + '/ordenes/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  }).then(res => {
    if (res.status === 201) {
      res.json().then(data => pedirURLPago(data.orden_uuid));
    } else {
      res.json().then(error => {
        document.getElementById('mensaje-pago').innerText = "❌ Error: " + (error.error || "Verifica tus datos");
      });
    }
  });
}

function pedirURLPago(ordenUUID) {
  const form = new FormData();
  form.append("orden_uuid", ordenUUID);

  fetch(API_BASE + '/pagos/', {
    method: 'POST',
    body: form
  }).then(res => {
    if (res.status === 201) {
      res.json().then(data => {
        window.location.href = data.url_pago + "?token_ws=" + data.token;
      });
    } else {
      alert("❌ Error al generar link de pago.");
    }
  });
}

function crearProducto(event) {
  event.preventDefault();

  const form = new FormData(document.getElementById('form-nuevo-producto'));
  fetch(API_BASE + '/productos/', {
    method: 'POST',
    body: form
  }).then(res => {
    const mensaje = document.getElementById('mensaje-admin');
    if (res.status === 201) {
      mensaje.innerText = '✅ Producto creado con éxito';
      document.getElementById('form-nuevo-producto').reset();
    } else {
      res.json().then(data => {
        mensaje.innerText = '❌ Error: ' + (data.error || 'no se pudo crear');
      });
    }
  });
}

const queryMenu = `
  query ObtenerMenuLaChilena {
    empanadas {
      id
      sabor
      tipoCoccion
      precio
      disponible
    }
  }
`;

const queryCliente = `
  query ObtenerDatosCliente($run: String!) {
    cliente(run: $run) {
      run
      nombreCompleto
      direccion
      comuna
      correoElectronico
      numeroTelefonico
    }
  }
`;

const queryReporteVentas = `
  query ReporteVentas {
    ventasWeb {
      idPedido
      fecha
      total
      estadoPago
    }
  }
`;

const formulario = document.getElementById('form-registro');

if (formulario) {
    formulario.addEventListener('submit', function(event) {
        event.preventDefault();
        console.log("Validando correo mediante API externa...");
    });
}

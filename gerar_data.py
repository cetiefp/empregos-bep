function formatarData(dataStr) {
  if (!dataStr) return '';

  // tenta converter formato português (dd-mm-yyyy)
  const partes = dataStr.split(/[-\/]/);

  if (partes.length === 3) {
    const data = new Date(`${partes[2]}-${partes[1]}-${partes[0]}`);
    return data.toLocaleDateString('pt-PT');
  }

  return dataStr; // fallback
}

fetch('data.json')
  .then(response => response.json())
  .then(data => {
    const container = document.getElementById('ofertas');

    data.forEach(oferta => {
      const div = document.createElement('div');
      div.innerHTML = `
        <h3>${oferta.titulo}</h3>
        <p><strong>Entidade:</strong> ${oferta.entidade}</p>
        <p><strong>Data:</strong> ${formatarData(oferta.data)}</p>
        <a href="${oferta.url}" target="_blank">Ver oferta</a>
        <hr>
      `;
      container.appendChild(div);
    });
  });

fetch('data.json')
  .then(response => response.json())
  .then(data => {

    // ordenar por data (mais recente primeiro)
    data.sort((a, b) => new Date(b.data) - new Date(a.data));

    mostrarEmpregos(data);

    // pesquisa
    const searchInput = document.getElementById('search');

    searchInput.addEventListener('input', function () {
      const termo = this.value.toLowerCase();

      const filtrado = data.filter(emprego =>
        emprego.titulo.toLowerCase().includes(termo) ||
        emprego.entidade.toLowerCase().includes(termo) ||
        emprego.local.toLowerCase().includes(termo)
      );

      mostrarEmpregos(filtrado);
    });
  })
  .catch(error => {
    console.error('Erro ao carregar data.json:', error);
  });

function mostrarEmpregos(lista) {
  const ul = document.getElementById('lista-empregos');
  ul.innerHTML = '';

  lista.forEach(emprego => {
    const li = document.createElement('li');

    li.innerHTML = `
      <a href="${emprego.link}" target="_blank">
        <strong>${emprego.titulo}</strong><br>
        ${emprego.entidade} — ${emprego.local}<br>
        <small>${formatarData(emprego.data)}</small>
      </a>
    `;

    ul.appendChild(li);
  });
}

// ✅ função que faltava antes
function formatarData(dataStr) {
  const data = new Date(dataStr);
  return data.toLocaleDateString('pt-PT');
}

fetch("data.json")
  .then(response => response.json())
  .then(data => {
    const container = document.getElementById("conteudo");
    container.innerHTML = "";

    data.forEach(oferta => {
      const div = document.createElement("div");

      div.innerHTML = `
        <h3><a href="${oferta.link}" target="_blank">${oferta.titulo}</a></h3>
        <p><strong>${oferta.entidade}</strong></p>
        <p>Data: ${oferta.data}</p>
        <hr>
      `;

      container.appendChild(div);
    });
  })
  .catch(error => {
    document.getElementById("conteudo").innerText = "Erro ao carregar dados.";
    console.error(error);
  });

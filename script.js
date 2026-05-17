fetch("data.json")
  .then(r => r.json())
  .then(data => {
    const div = document.getElementById("conteudo");
    div.innerHTML = "";

    data.forEach(o => {
      const item = document.createElement("div");

      item.innerHTML = `
        <h3><a href="${o.link}" target="_blank">${o.titulo}</a></h3>
        <p><strong>${o.entidade}</strong></p>
        <p>Data: ${o.data}</p>
        <hr>
      `;

      div.appendChild(item);
    });
  })
  .catch(() => {
    document.getElementById("conteudo").innerText = "Erro a carregar dados.";
  });


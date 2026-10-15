(function () {
  const b = document.getElementById("lookupBtn");
  if (!b) return;
  b.addEventListener("click", async function () {
    const a = document.getElementById("account").value.trim();
    if (!/^\d{8}$/.test(a)) {
      alert("A conta deve ter exatamente 8 dígitos numéricos.");
      return;
    }
    const f = new FormData();
    f.append("account", a);
    const r = await fetch("../requests/lookup", { method: "POST", body: f });
    const p = await r.json();
    if (!r.ok || !p.ok) {
      alert(p.message || "Erro na consulta.");
      return;
    }
    Object.entries(p.data).forEach(([k, v]) => {
      const e =
        document.getElementById(k) || document.querySelector(`[name="${k}"]`);
      if (e) e.value = v || "";
    });
  });
})();

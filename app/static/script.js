function getVal(id)  { return document.getElementById(id)?.value.trim(); }
function getRadio(name) {
  const el = document.querySelector(`input[name="${name}"]:checked`);
  return el ? el.value : null;
}
function markInvalid(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add("invalid");
}
function clearInvalid() {
  document.querySelectorAll(".invalid").forEach(e => e.classList.remove("invalid"));
}

function validateForm() {
  const rules = [
    { id: "CreditScore",     min: 300, max: 850,  label: "Score de crédit (300–850)" },
    { id: "Age",             min: 18,  max: 100,  label: "Âge (18–100)" },
    { id: "Tenure",          min: 0,   max: 10,   label: "Ancienneté (0–10)" },
    { id: "NumOfProducts",   min: 1,   max: 4,    label: "Nombre de produits (1–4)" },
    { id: "Balance",         min: 0,   max: null, label: "Solde bancaire" },
    { id: "EstimatedSalary", min: 0,   max: null, label: "Salaire estimé" },
  ];
  const errors = [];
  rules.forEach(({ id, min, max, label }) => {
    const val = parseFloat(getVal(id));
    if (isNaN(val)) { errors.push(`${label} est requis.`); markInvalid(id); return; }
    if (min !== null && val < min) { errors.push(`${label} : valeur trop basse (min ${min}).`); markInvalid(id); }
    if (max !== null && val > max) { errors.push(`${label} : valeur trop élevée (max ${max}).`); markInvalid(id); }
  });
  if (!getVal("Geography")) { errors.push("Veuillez sélectionner un pays."); markInvalid("Geography"); }
  if (!getVal("Gender"))    { errors.push("Veuillez sélectionner un genre."); markInvalid("Gender"); }
  return errors;
}

function showToast(msg) {
  const t = document.getElementById("errorToast");
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 4500);
}

async function submitPrediction() {
  clearInvalid();
  const errors = validateForm();
  if (errors.length) { showToast("⚠  " + errors[0]); return; }

  const btn = document.getElementById("submitBtn");
  const lbl = btn.querySelector(".btn-label");
  btn.disabled = true;
  lbl.textContent = "Analyse en cours…";

  const payload = {
    client_name:     getVal("client_name") || "Client",
    CreditScore:     parseInt(getVal("CreditScore")),
    Geography:       getVal("Geography"),
    Gender:          getVal("Gender"),
    Age:             parseInt(getVal("Age")),
    Tenure:          parseInt(getVal("Tenure")),
    Balance:         parseFloat(getVal("Balance")),
    NumOfProducts:   parseInt(getVal("NumOfProducts")),
    HasCrCard:       parseInt(getRadio("HasCrCard")),
    IsActiveMember:  parseInt(getRadio("IsActiveMember")),
    EstimatedSalary: parseFloat(getVal("EstimatedSalary")),
  };

  try {
    const resp = await fetch("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await resp.json();
    if (!data.success) { showToast("Erreur : " + data.error); return; }
    displayResult(data);
  } catch (err) {
    showToast("Erreur réseau. Vérifiez que le serveur est actif.");
    console.error(err);
  } finally {
    btn.disabled = false;
    lbl.textContent = "Lancer l'analyse";
  }
}

function displayResult(data) {
  const tier      = data.risk_tier;                             // "low" | "medium" | "high"
  const tierClass = "risk-" + (tier === "medium" ? "med" : tier);
  const prob      = data.probability;
  const setText = (id, value) => {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  };

  // Header verdict
  setText("verdictLabel", data.label);

  // Client block
  setText("resultName", data.client_name);
  setText("predClass", data.prediction);
  setText("predLabel", data.label);

  // Model block
  setText("resultModel", data.model_used);
  setText("resultAccuracy", data.model_accuracy);
  setText("resultRocAuc", data.model_roc_auc);

  // Probability block
  const probNum = document.getElementById("probValue");
  probNum.textContent = prob.toFixed(1) + "%";
  probNum.className   = "prob-number " + tierClass;

  const tierLabels = { low: "Risque faible", medium: "Risque moyen", high: "Risque élevé" };
  const badge = document.getElementById("probTierBadge");
  badge.textContent = tierLabels[tier];
  badge.className   = "prob-tier-badge " + tierClass;

  const bar = document.getElementById("probBar");
  bar.style.width = "0%";
  bar.className   = "prob-bar-fill " + tierClass;
  setTimeout(() => { bar.style.width = prob + "%"; }, 80);

  // Explanation
  document.getElementById("expMain").textContent =
    `Le modèle estime une probabilité de quitter de ${prob.toFixed(1)}%.`;

  // Show result
  document.getElementById("formCard").style.display   = "none";
  document.getElementById("resultCard").style.display = "block";
  document.getElementById("resultCard").scrollIntoView({ behavior: "smooth", block: "start" });
}

function resetForm() {
  clearInvalid();
  document.getElementById("resultCard").style.display = "none";
  document.getElementById("formCard").style.display   = "block";
  document.getElementById("formCard").scrollIntoView({ behavior: "smooth" });
}

document.addEventListener("keydown", e => {
  if (e.key === "Enter" && document.getElementById("formCard").style.display !== "none") {
    submitPrediction();
  }
});

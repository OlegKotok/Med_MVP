const form = document.querySelector("#patient-form");
const message = document.querySelector("#message");

function showMessage(text, type) {
  message.textContent = text;
  message.className = `message ${type}`;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const submitButton = form.querySelector("button");
  submitButton.disabled = true;
  showMessage("", "");

  const payload = {
    full_name: form.full_name.value.trim(),
    birth_date: form.birth_date.value,
  };

  try {
    const response = await fetch("/patients", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      showMessage("Check the entered patient data and try again.", "error");
      return;
    }

    const patient = await response.json();
    showMessage(`Created patient #${patient.id}: ${patient.full_name}`, "success");
    form.reset();
  } catch {
    showMessage("The API is unavailable. Try again later.", "error");
  } finally {
    submitButton.disabled = false;
  }
});

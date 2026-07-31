const state = {
  access: localStorage.getItem("swiftcore_access") || "",
  refresh: localStorage.getItem("swiftcore_refresh") || "",
};

const sessionStatus = document.querySelector("#sessionStatus");
const logoutBtn = document.querySelector("#logoutBtn");
const registerForm = document.querySelector("#registerForm");
const loginForm = document.querySelector("#loginForm");
const topUpForm = document.querySelector("#topUpForm");
const paymentForm = document.querySelector("#paymentForm");
const loadWalletBtn = document.querySelector("#loadWalletBtn");
const loadPaymentsBtn = document.querySelector("#loadPaymentsBtn");
const walletBalance = document.querySelector("#walletBalance");
const paymentsList = document.querySelector("#paymentsList");
const paymentsEmpty = document.querySelector("#paymentsEmpty");
const newKeyBtn = document.querySelector("#newKeyBtn");
const idempotencyInput = document.querySelector("#idempotencyInput");

function setMessage(id, text, type = "") {
  const element = document.querySelector(id);
  element.textContent = text;
  element.className = `form-message ${type}`.trim();
}

function updateSession() {
  sessionStatus.textContent = state.access ? "Token saqlandi" : "Token yo'q";
}

function saveTokens(data) {
  state.access = data.access;
  state.refresh = data.refresh;
  localStorage.setItem("swiftcore_access", state.access);
  localStorage.setItem("swiftcore_refresh", state.refresh);
  updateSession();
}

function clearTokens() {
  state.access = "";
  state.refresh = "";
  localStorage.removeItem("swiftcore_access");
  localStorage.removeItem("swiftcore_refresh");
  updateSession();
}

function authHeaders(extra = {}) {
  if (!state.access) {
    throw new Error("Avval login qiling.");
  }
  return {
    Authorization: `Bearer ${state.access}`,
    ...extra,
  };
}

async function apiRequest(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = data.detail || JSON.stringify(data);
    throw new Error(message);
  }
  return data;
}

function formData(form) {
  return Object.fromEntries(new FormData(form).entries());
}

function generateIdempotencyKey() {
  return `pay-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;
}

function renderWallet(wallet) {
  walletBalance.textContent = `${wallet.balance} ${wallet.currency.toUpperCase()}`;
}

function renderPayments(payments) {
  paymentsList.innerHTML = "";
  paymentsEmpty.style.display = payments.length ? "none" : "block";

  payments.forEach((payment) => {
    const item = document.createElement("article");
    item.className = "payment-item";
    item.innerHTML = `
      <div>
        <strong>${payment.amount} ${payment.currency.toUpperCase()}</strong>
        <div class="payment-meta">Key: ${payment.idempotency_key}</div>
        <div class="payment-meta">${new Date(payment.created_at).toLocaleString()}</div>
      </div>
      <span class="status-pill ${payment.status}">${payment.status}</span>
    `;
    paymentsList.appendChild(item);
  });
}

registerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setMessage("#registerMessage", "Creating account...");
  try {
    const payload = formData(registerForm);
    await apiRequest("/api/auth/register/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    setMessage("#registerMessage", "Account created. Login now.", "success");
    registerForm.reset();
  } catch (error) {
    setMessage("#registerMessage", error.message, "error");
  }
});

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setMessage("#loginMessage", "Getting token...");
  try {
    const payload = formData(loginForm);
    const data = await apiRequest("/api/auth/token/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    saveTokens(data);
    setMessage("#loginMessage", "Token saved.", "success");
    await loadWallet();
    await loadPayments();
  } catch (error) {
    setMessage("#loginMessage", error.message, "error");
  }
});

async function loadWallet() {
  const wallet = await apiRequest("/api/wallet/", {
    headers: authHeaders(),
  });
  renderWallet(wallet);
}

loadWalletBtn.addEventListener("click", async () => {
  try {
    await loadWallet();
  } catch (error) {
    setMessage("#topUpMessage", error.message, "error");
  }
});

topUpForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setMessage("#topUpMessage", "Adding funds...");
  try {
    const payload = formData(topUpForm);
    const wallet = await apiRequest("/api/wallet/top-up/", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(payload),
    });
    renderWallet(wallet);
    setMessage("#topUpMessage", "Balance updated.", "success");
  } catch (error) {
    setMessage("#topUpMessage", error.message, "error");
  }
});

async function loadPayments() {
  const payments = await apiRequest("/api/payments/", {
    headers: authHeaders(),
  });
  renderPayments(payments);
}

loadPaymentsBtn.addEventListener("click", async () => {
  try {
    await loadPayments();
  } catch (error) {
    setMessage("#paymentMessage", error.message, "error");
  }
});

newKeyBtn.addEventListener("click", () => {
  idempotencyInput.value = generateIdempotencyKey();
});

paymentForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setMessage("#paymentMessage", "Creating payment...");
  try {
    const payload = formData(paymentForm);
    const payment = await apiRequest("/api/payments/", {
      method: "POST",
      headers: authHeaders({ "Idempotency-Key": payload.idempotencyKey }),
      body: JSON.stringify({
        amount: payload.amount,
        currency: payload.currency,
      }),
    });
    setMessage("#paymentMessage", `Payment ${payment.status}.`, "success");
    await loadWallet();
    await loadPayments();
  } catch (error) {
    setMessage("#paymentMessage", error.message, "error");
  }
});

logoutBtn.addEventListener("click", () => {
  clearTokens();
  walletBalance.textContent = "0.00 UZS";
  renderPayments([]);
});

idempotencyInput.value = generateIdempotencyKey();
updateSession();


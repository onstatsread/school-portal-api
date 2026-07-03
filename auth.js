// ── Shared auth helpers — included in every dashboard page ──────────────────

const API_BASE = "https://YOUR-APP-NAME.onrender.com"; // ← Same as index.html

function getToken()    { return localStorage.getItem("token"); }
function getRole()     { return localStorage.getItem("role"); }
function getFullName() { return localStorage.getItem("full_name"); }
function getUserId()   { return localStorage.getItem("user_id"); }

function requireAuth(expectedRole = null) {
  const token = getToken();
  const role  = getRole();
  if (!token || !role) {
    window.location.href = "../index.html";
    return false;
  }
  if (expectedRole && role !== expectedRole) {
    alert("Access denied. Wrong role.");
    window.location.href = "../index.html";
    return false;
  }
  return true;
}

function logout() {
  localStorage.clear();
  window.location.href = "../index.html";
}

async function apiFetch(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${getToken()}`,
      ...(options.headers || {})
    }
  });

  if (res.status === 401) {
    logout();
    return null;
  }

  return res;
}

function showMsg(elId, msg, isError = false) {
  const el = document.getElementById(elId);
  if (!el) return;
  el.textContent = msg;
  el.style.display = "block";
  el.style.background = isError ? "#ffebee" : "#e8f5e9";
  el.style.color      = isError ? "#c62828" : "#2e7d32";
  el.style.border     = isError ? "1px solid #ef9a9a" : "1px solid #a5d6a7";
}

function formatDate(d) {
  if (!d) return "";
  return new Date(d).toLocaleDateString("en-GB");
}

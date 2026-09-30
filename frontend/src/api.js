const listeners = new Set();
export const onTrace = (fn) => {
  listeners.add(fn);
  return () => listeners.delete(fn);
};

async function call(method, path, { body, token } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Token ${token}`;
  const started = performance.now();
  const res = await fetch(`/api${path}`, { method, headers, body: body && JSON.stringify(body) });
  const data = await res.json().catch(() => null);
  const shown = token ? { ...headers, Authorization: `Token …${token.slice(-6)}` } : headers;
  listeners.forEach((fn) =>
    fn({ method, path: `/api${path}`, status: res.status, ms: Math.round(performance.now() - started), request: { headers: shown, body }, data })
  );
  if (!res.ok) throw Object.assign(new Error(`HTTP ${res.status}`), { errors: data?.errors });
  return data;
}

export const errorsOf = (err) => err.errors ?? { conexión: ["no se pudo contactar con la API"] };
export const register = (user) => call("POST", "/users", { body: { user } });
export const login = (user) => call("POST", "/users/login", { body: { user } });
export const createArticle = (article, token) => call("POST", "/articles", { body: { article }, token });

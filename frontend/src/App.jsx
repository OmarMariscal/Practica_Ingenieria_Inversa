import { useEffect, useState } from "react";
import * as api from "./api.js";

const hide = (k, v) => (k === "token" ? `…${String(v).slice(-6)}` : k === "password" ? "••••••••" : v);
const pretty = (v) => JSON.stringify(v, hide, 2);

function Problems({ errors }) {
  const items = Object.entries(errors).flatMap(([field, msgs]) => msgs.map((m) => `${field}: ${m}`));
  if (!items.length) return null;
  return (
    <ul className="problems" role="alert">
      {items.map((t) => (
        <li key={t}>{t}</li>
      ))}
    </ul>
  );
}

function AuthPanel({ onAuth }) {
  const [mode, setMode] = useState("register");
  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [errors, setErrors] = useState({});
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setErrors({});
    try {
      const { user } =
        mode === "register"
          ? await api.register(form)
          : await api.login({ email: form.email, password: form.password });
      onAuth({ username: user.username, token: user.token });
    } catch (err) {
      setErrors(api.errorsOf(err));
    }
  }

  return (
    <form className="card" onSubmit={submit}>
      <div className="tabs" role="tablist">
        {[["register", "Crear cuenta"], ["login", "Iniciar sesión"]].map(([id, label]) => (
          <button key={id} type="button" role="tab" aria-selected={mode === id} onClick={() => { setMode(id); setErrors({}); }}>
            {label}
          </button>
        ))}
      </div>
      {mode === "register" && (
        <label>Nombre de usuario<input value={form.username} onChange={set("username")} required minLength={3} autoComplete="username" /></label>
      )}
      <label>Correo<input type="email" value={form.email} onChange={set("email")} required autoComplete="email" /></label>
      <label>Contraseña<input type="password" value={form.password} onChange={set("password")} required minLength={mode === "register" ? 8 : 1} autoComplete={mode === "register" ? "new-password" : "current-password"} /></label>
      <Problems errors={errors} />
      <button className="primary">{mode === "register" ? "Crear cuenta" : "Iniciar sesión"}</button>
    </form>
  );
}

const EMPTY = { title: "", description: "", body: "", tags: "" };

function ArticleForm({ token, onCreated }) {
  const [f, setF] = useState(EMPTY);
  const [errors, setErrors] = useState({});
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setErrors({});
    setBusy(true);
    try {
      const tagList = f.tags.split(",").map((t) => t.trim()).filter(Boolean);
      const { article } = await api.createArticle({ title: f.title, description: f.description, body: f.body, tagList }, token);
      onCreated(article);
      setF(EMPTY);
    } catch (err) {
      setErrors(api.errorsOf(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="card" onSubmit={submit}>
      <h2>Nuevo artículo</h2>
      <label>Título<input value={f.title} onChange={set("title")} maxLength={150} /></label>
      <label>Descripción<input value={f.description} onChange={set("description")} /></label>
      <label>Contenido<textarea rows={6} value={f.body} onChange={set("body")} /></label>
      <label>Etiquetas, separadas por comas<input value={f.tags} onChange={set("tags")} placeholder="python, apis" /></label>
      <Problems errors={errors} />
      <button className="primary" disabled={busy}>{busy ? "Publicando…" : "Publicar artículo"}</button>
    </form>
  );
}

function Result({ article }) {
  return (
    <section className="card result" aria-live="polite">
      <h2>Artículo publicado</h2>
      <p className="title">{article.title}</p>
      <dl>
        <dt>Slug</dt><dd>{article.slug}</dd>
        <dt>Autor</dt><dd>{article.author.username}</dd>
        <dt>Etiquetas</dt><dd>{article.tagList.join(", ") || "sin etiquetas"}</dd>
        <dt>Creado</dt><dd>{new Date(article.createdAt).toLocaleString()}</dd>
      </dl>
    </section>
  );
}

function Trace({ trace }) {
  if (!trace)
    return (
      <aside className="trace">
        <h2>Traza HTTP</h2>
        <p className="hint">Aquí aparece cada petición que envía la interfaz y la respuesta exacta de la API.</p>
      </aside>
    );
  const kind = trace.status >= 500 ? "bad" : trace.status >= 400 ? "warn" : "ok";
  return (
    <aside className="trace">
      <h2>Traza HTTP</h2>
      <p className="line">
        <b>{trace.method}</b> {trace.path} <span className={`chip ${kind}`}>{trace.status}</span>
        <span className="ms">{trace.ms} ms</span>
      </p>
      <h3>Petición</h3>
      <pre>{pretty(trace.request)}</pre>
      <h3>Respuesta</h3>
      <pre>{pretty(trace.data)}</pre>
    </aside>
  );
}

export default function App() {
  const [session, setSession] = useState(() => {
    try { return JSON.parse(sessionStorage.getItem("session")); } catch { return null; }
  });
  const [trace, setTrace] = useState(null);
  const [created, setCreated] = useState(null);
  useEffect(() => api.onTrace(setTrace), []);

  const start = (s) => { sessionStorage.setItem("session", JSON.stringify(s)); setSession(s); };
  const leave = () => { sessionStorage.removeItem("session"); setSession(null); setCreated(null); };

  return (
    <div className="shell">
      <main>
        <header>
          <h1>Consola de artículos</h1>
          <p>Crea un artículo y comprueba qué recibió y qué devolvió la API.</p>
          {session && (
            <p className="who">Sesión de <b>{session.username}</b> <button className="link" onClick={leave}>Cerrar sesión</button></p>
          )}
        </header>
        {session ? <ArticleForm token={session.token} onCreated={setCreated} /> : <AuthPanel onAuth={start} />}
        {created && <Result article={created} />}
      </main>
      <Trace trace={trace} />
    </div>
  );
}

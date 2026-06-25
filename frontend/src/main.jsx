import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Link, NavLink, Route, Routes, useParams } from 'react-router-dom';
import './styles.css';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';
const MODEL_OPTIONS = ['tfidf', 'textrank', 'bart', 't5'];

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options
  });
  if (!response.ok) {
    let detail = '';
    try {
      const body = await response.json();
      detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail || body);
    } catch {
      detail = await response.text();
    }
    throw new Error(`Request failed: ${response.status}${detail ? ` - ${detail}` : ''}`);
  }
  return response.json();
}

function useApi(path, initialValue) {
  const [data, setData] = useState(initialValue);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    api(path)
      .then((result) => active && setData(result))
      .catch((err) => active && setError(err.message))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [path]);

  return { data, error, loading, setData };
}

function Shell() {
  return (
    <BrowserRouter>
      <header className="topbar">
        <Link className="brand" to="/">News Summarizer</Link>
        <nav>
          <NavLink to="/">Articles</NavLink>
          <NavLink to="/search">Search</NavLink>
          <NavLink to="/ingest">Ingest</NavLink>
          <NavLink to="/stats">Stats</NavLink>
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/articles/:id" element={<ArticleDetail />} />
          <Route path="/search" element={<Search />} />
          <Route path="/ingest" element={<Ingest />} />
          <Route path="/stats" element={<Stats />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}

function Home() {
  const { data, error, loading } = useApi('/articles?limit=25', []);
  return (
    <section>
      <h1>Latest Articles</h1>
      <Status loading={loading} error={error} />
      <ArticleList articles={data} />
    </section>
  );
}

function ArticleList({ articles }) {
  if (!articles.length) return <p className="empty">No articles found.</p>;
  return (
    <div className="list">
      {articles.map((article) => (
        <article className="item" key={article.id}>
          <Link to={`/articles/${article.id}`}>{article.title}</Link>
          <div className="meta">{[article.source, article.category, article.published_at].filter(Boolean).join(' | ')}</div>
        </article>
      ))}
    </div>
  );
}

function ArticleDetail() {
  const { id } = useParams();
  const { data: article, error, loading } = useApi(`/articles/${id}`, null);
  const summaries = article?.summaries || [];

  return (
    <section>
      <Status loading={loading} error={error} />
      {article && (
        <>
          <h1>{article.title}</h1>
          <div className="meta">{[article.source, article.category, article.published_at].filter(Boolean).join(' | ')}</div>
          <h2>Full Text</h2>
          <p className="article-text">{article.full_text || 'No full text stored.'}</p>
          <h2>Summaries</h2>
          <div className="list">
            {summaries.map((summary) => (
              <article className="item" key={summary.id}>
                <strong>{summary.model_name}</strong>
                <p>{summary.summary_text}</p>
                <div className="meta">{summary.summary_type} | {summary.summary_length} words | {formatNumber(summary.processing_time)}s</div>
              </article>
            ))}
          </div>
        </>
      )}
    </section>
  );
}

function Search() {
  const [query, setQuery] = useState('');
  const [articles, setArticles] = useState([]);
  const [status, setStatus] = useState('');

  async function submit(event) {
    event.preventDefault();
    if (!query.trim()) return;
    setStatus('Searching...');
    try {
      setArticles(await api(`/search?q=${encodeURIComponent(query)}`));
      setStatus('');
    } catch (err) {
      setStatus(err.message);
    }
  }

  return (
    <section>
      <h1>Search</h1>
      <form className="toolbar" onSubmit={submit}>
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Keyword" />
        <button type="submit">Search</button>
      </form>
      {status && <p className="empty">{status}</p>}
      <ArticleList articles={articles} />
    </section>
  );
}

function Ingest() {
  const [limit, setLimit] = useState('');
  const [source, setSource] = useState('');
  const { data: sources } = useApi('/sources', []);
  const [forceRefresh, setForceRefresh] = useState(false);
  const [models, setModels] = useState(['tfidf']);
  const [result, setResult] = useState(null);
  const [status, setStatus] = useState('');

  function toggleModel(model) {
    setModels((current) => current.includes(model) ? current.filter((item) => item !== model) : [...current, model]);
  }

  async function submit(event) {
    event.preventDefault();
    setStatus('Running ingestion...');
    try {
      const payload = {
        limit: limit ? Number(limit) : null,
        source: source || null,
        force_refresh: forceRefresh,
        models
      };
      setResult(await api('/ingest', { method: 'POST', body: JSON.stringify(payload) }));
      setStatus('');
    } catch (err) {
      setStatus(err.message);
    }
  }

  return (
    <section>
      <h1>Ingest</h1>
      <form className="panel" onSubmit={submit}>
        <label>Limit<input type="number" min="1" value={limit} onChange={(event) => setLimit(event.target.value)} /></label>
        <label>
          Source
          <select value={source} onChange={(event) => setSource(event.target.value)}>
            <option value="">All sources</option>
            {sources.map((item) => (
              <option key={item.name} value={item.name} disabled={!item.enabled}>
                {item.name}{item.enabled ? '' : ' (disabled)'}
              </option>
            ))}
          </select>
        </label>
        <label className="check"><input type="checkbox" checked={forceRefresh} onChange={(event) => setForceRefresh(event.target.checked)} /> Force refresh</label>
        <div className="checks">
          {MODEL_OPTIONS.map((model) => (
            <label className="check" key={model}>
              <input type="checkbox" checked={models.includes(model)} onChange={() => toggleModel(model)} />
              {model}
            </label>
          ))}
        </div>
        <button type="submit">Run Ingest</button>
      </form>
      {status && <p className="empty">{status}</p>}
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </section>
  );
}

function Stats() {
  const { data, error, loading } = useApi('/models/stats', null);
  const rows = data?.summaries_by_model || [];
  return (
    <section>
      <h1>Monitoring</h1>
      <Status loading={loading} error={error} />
      {data && (
        <>
          <div className="metrics">
            <div><span>Total Articles</span><strong>{data.total_articles}</strong></div>
            <div><span>Total Summaries</span><strong>{data.total_summaries}</strong></div>
            <div><span>Latest Ingest</span><strong>{data.latest_ingestion_time || 'None'}</strong></div>
          </div>
          <ModelTable rows={rows} />
        </>
      )}
    </section>
  );
}

function ModelTable({ rows }) {
  if (!rows.length) return <p className="empty">No model data yet.</p>;
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Model</th>
            <th>Summaries</th>
            <th>Avg Time</th>
            <th>Avg Length</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.model_name}>
              <td>{row.model_name}</td>
              <td>{row.num_summaries}</td>
              <td>{formatNumber(row.average_processing_time)}</td>
              <td>{formatNumber(row.average_summary_length)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Status({ loading, error }) {
  if (loading) return <p className="empty">Loading...</p>;
  if (error) return <p className="error">{error}</p>;
  return null;
}

function formatNumber(value) {
  if (value === null || value === undefined) return '-';
  return Number(value).toFixed(3);
}

createRoot(document.getElementById('root')).render(<Shell />);

const BASE_URL = 'http://127.0.0.1:8000'

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const body = await res.text()
    throw new Error(`${res.status} ${res.statusText}: ${body}`)
  }
  return res.json()
}

export const api = {
  getWatchlist: () => request('/watchlist'),
  getDiff: () => request('/watchlist/diff'),
  addItem: (item) =>
    request('/watchlist', { method: 'POST', body: JSON.stringify(item) }),
  deleteItem: (id) => request(`/watchlist/${id}`, { method: 'DELETE' }),
}

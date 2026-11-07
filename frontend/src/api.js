const BASE = '/api/items';

async function request(url, options) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.message || 'Error en la petición');
  }
  return res.status === 204 ? null : res.json();
}

export const getItems = () => request(BASE);
export const createItem = (item) => request(BASE, { method: 'POST', body: JSON.stringify(item) });
export const updateItem = (id, data) => request(`${BASE}/${id}`, { method: 'PATCH', body: JSON.stringify(data) });
export const deleteItem = (id) => request(`${BASE}/${id}`, { method: 'DELETE' });

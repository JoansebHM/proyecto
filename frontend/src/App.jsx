import { useEffect, useState } from 'react';
import { getItems, createItem, updateItem, deleteItem } from './api.js';

const money = (n) =>
  n.toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 });

const emptyForm = { name: '', quantity: 1, price: '' };

export default function App() {
  const [items, setItems] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [draft, setDraft] = useState(emptyForm);

  const run = async (fn) => {
    try {
      setError('');
      await fn();
    } catch (e) {
      setError(e.message);
    }
  };

  const load = () => run(async () => setItems(await getItems()));
  useEffect(() => { load(); }, []);

  const add = (e) => {
    e.preventDefault();
    run(async () => {
      await createItem({ name: form.name, quantity: Number(form.quantity), price: Number(form.price) });
      setForm(emptyForm);
      await load();
    });
  };

  const toggle = (item) => run(async () => { await updateItem(item.id, { purchased: !item.purchased }); await load(); });
  const remove = (item) => run(async () => { await deleteItem(item.id); await load(); });

  const startEdit = (i) => {
    setEditingId(i.id);
    setDraft({ name: i.name, quantity: i.quantity, price: i.price });
  };
  const saveEdit = (e) => {
    e.preventDefault();
    run(async () => {
      await updateItem(editingId, { name: draft.name, quantity: Number(draft.quantity), price: Number(draft.price) });
      setEditingId(null);
      await load();
    });
  };

  const subtotal = (i) => i.quantity * i.price;
  const total = items.reduce((s, i) => s + subtotal(i), 0);
  const spent = items.filter((i) => i.purchased).reduce((s, i) => s + subtotal(i), 0);

  return (
    <main className="app">
      <h1>🛒 Lista de mercado</h1>

      <section className="summary">
        <div><span>Total estimado</span><strong>{money(total)}</strong></div>
        <div><span>Gastado</span><strong className="spent">{money(spent)}</strong></div>
        <div><span>Pendiente</span><strong>{money(total - spent)}</strong></div>
      </section>

      <form className="form" onSubmit={add}>
        <input placeholder="Producto" value={form.name} required
          onChange={(e) => setForm({ ...form, name: e.target.value })} />
        <input type="number" min="1" step="1" placeholder="Cant." value={form.quantity} required
          onChange={(e) => setForm({ ...form, quantity: e.target.value })} />
        <input type="number" min="0" step="any" placeholder="Precio unidad" value={form.price} required
          onChange={(e) => setForm({ ...form, price: e.target.value })} />
        <button type="submit">Agregar</button>
      </form>

      {error && <p className="error">{error}</p>}

      {items.length === 0 ? (
        <p className="empty">Tu lista está vacía. Agrega tu primer producto.</p>
      ) : (
        <ul className="list">
          {items.map((i) =>
            editingId === i.id ? (
              <li key={i.id}>
                <form className="form edit" onSubmit={saveEdit}>
                  <input value={draft.name} required autoFocus
                    onChange={(e) => setDraft({ ...draft, name: e.target.value })} />
                  <input type="number" min="1" step="1" value={draft.quantity} required
                    onChange={(e) => setDraft({ ...draft, quantity: e.target.value })} />
                  <input type="number" min="0" step="any" value={draft.price} required
                    onChange={(e) => setDraft({ ...draft, price: e.target.value })} />
                  <button type="submit" title="Guardar">✓</button>
                  <button type="button" className="cancel" title="Cancelar" onClick={() => setEditingId(null)}>✕</button>
                </form>
              </li>
            ) : (
              <li key={i.id} className={i.purchased ? 'done' : ''}>
                <input type="checkbox" checked={i.purchased} onChange={() => toggle(i)} title="Marcar como comprado" />
                <div className="info">
                  <span className="name">{i.name}</span>
                  <small>{i.quantity} × {money(i.price)}</small>
                </div>
                <strong>{money(subtotal(i))}</strong>
                <button className="del" onClick={() => startEdit(i)} title="Editar">✏️</button>
                <button className="del" onClick={() => remove(i)} title="Eliminar">✕</button>
              </li>
            )
          )}
        </ul>
      )}
    </main>
  );
}

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { getItems, createItem, updateItem, deleteItem } from './api.js';

const ok = (body, status = 200) => ({ ok: true, status, json: async () => body });

describe('api', () => {
  beforeEach(() => { global.fetch = vi.fn(); });
  afterEach(() => vi.restoreAllMocks());

  it('getItems hace GET a /api/items y devuelve el JSON', async () => {
    fetch.mockResolvedValue(ok([{ id: 1 }]));
    expect(await getItems()).toEqual([{ id: 1 }]);
    expect(fetch.mock.calls[0][0]).toBe('/api/items');
  });

  it('createItem hace POST con el body', async () => {
    const item = { name: 'A', quantity: 1, price: 2 };
    fetch.mockResolvedValue(ok({ id: 1, ...item }));
    await createItem(item);
    const [url, opts] = fetch.mock.calls[0];
    expect(url).toBe('/api/items');
    expect(opts.method).toBe('POST');
    expect(JSON.parse(opts.body)).toEqual(item);
  });

  it('updateItem hace PATCH a /api/items/:id', async () => {
    fetch.mockResolvedValue(ok({ id: 5 }));
    await updateItem(5, { purchased: true });
    const [url, opts] = fetch.mock.calls[0];
    expect(url).toBe('/api/items/5');
    expect(opts.method).toBe('PATCH');
    expect(JSON.parse(opts.body)).toEqual({ purchased: true });
  });

  it('deleteItem hace DELETE y devuelve null con 204', async () => {
    fetch.mockResolvedValue({ ok: true, status: 204 });
    expect(await deleteItem(7)).toBeNull();
    expect(fetch.mock.calls[0][0]).toBe('/api/items/7');
    expect(fetch.mock.calls[0][1].method).toBe('DELETE');
  });

  it('lanza el mensaje del servidor si la respuesta no es ok', async () => {
    fetch.mockResolvedValue({ ok: false, json: async () => ({ message: 'El nombre es obligatorio' }) });
    await expect(createItem({})).rejects.toThrow('El nombre es obligatorio');
  });

  it('usa un mensaje genérico si el error no trae JSON', async () => {
    fetch.mockResolvedValue({ ok: false, json: async () => { throw new Error('x'); } });
    await expect(getItems()).rejects.toThrow('Error en la petición');
  });

  it('usa un mensaje genérico si el JSON no trae message', async () => {
    fetch.mockResolvedValue({ ok: false, json: async () => ({}) });
    await expect(getItems()).rejects.toThrow('Error en la petición');
  });
});

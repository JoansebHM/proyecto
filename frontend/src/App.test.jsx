import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App.jsx';
import * as api from './api.js';

vi.mock('./api.js');

const arroz = { id: 1, name: 'Arroz', quantity: 2, price: 1000, purchased: false };
const leche = { id: 2, name: 'Leche', quantity: 1, price: 3000, purchased: true };

// Los montos se formatean como COP; buscamos por dígitos para no depender del locale.
const summaryValue = (label) =>
  screen.getByText(label).parentElement.querySelector('strong').textContent.replace(/\D/g, '');

beforeEach(() => {
  vi.resetAllMocks();
  api.getItems.mockResolvedValue([]);
  api.createItem.mockResolvedValue({});
  api.updateItem.mockResolvedValue({});
  api.deleteItem.mockResolvedValue(null);
});

describe('App', () => {
  it('muestra el estado vacío sin productos', async () => {
    render(<App />);
    expect(await screen.findByText(/lista está vacía/i)).toBeInTheDocument();
  });

  it('lista los productos con cantidad y subtotal', async () => {
    api.getItems.mockResolvedValue([arroz]);
    render(<App />);
    expect(await screen.findByText('Arroz')).toBeInTheDocument();
    expect(screen.getByText(/2 ×/)).toBeInTheDocument();
  });

  it('calcula total, gastado y pendiente', async () => {
    api.getItems.mockResolvedValue([arroz, leche]); // 2000 pendiente + 3000 comprado
    render(<App />);
    await screen.findByText('Arroz');
    expect(summaryValue('Total estimado')).toBe('5000');
    expect(summaryValue('Gastado')).toBe('3000');
    expect(summaryValue('Pendiente')).toBe('2000');
  });

  it('agrega un producto y limpia el formulario', async () => {
    const user = userEvent.setup();
    render(<App />);
    await screen.findByText(/lista está vacía/i);
    await user.type(screen.getByPlaceholderText('Producto'), 'Pan');
    await user.clear(screen.getByPlaceholderText('Cant.'));
    await user.type(screen.getByPlaceholderText('Cant.'), '3');
    await user.type(screen.getByPlaceholderText('Precio unidad'), '1500');
    await user.click(screen.getByRole('button', { name: 'Agregar' }));
    await waitFor(() =>
      expect(api.createItem).toHaveBeenCalledWith({ name: 'Pan', quantity: 3, price: 1500 }));
    await waitFor(() => expect(screen.getByPlaceholderText('Producto')).toHaveValue(''));
    expect(screen.getByPlaceholderText('Cant.')).toHaveValue(1);
  });

  it('marca un producto como comprado', async () => {
    const user = userEvent.setup();
    api.getItems.mockResolvedValue([arroz]);
    render(<App />);
    await user.click(await screen.findByRole('checkbox'));
    expect(api.updateItem).toHaveBeenCalledWith(1, { purchased: true });
  });

  it('desmarca un producto comprado', async () => {
    const user = userEvent.setup();
    api.getItems.mockResolvedValue([leche]);
    render(<App />);
    await user.click(await screen.findByRole('checkbox'));
    expect(api.updateItem).toHaveBeenCalledWith(2, { purchased: false });
  });

  it('elimina un producto', async () => {
    const user = userEvent.setup();
    api.getItems.mockResolvedValue([arroz]);
    render(<App />);
    await user.click(await screen.findByTitle('Eliminar'));
    expect(api.deleteItem).toHaveBeenCalledWith(1);
  });

  it('edita un producto y guarda los cambios', async () => {
    const user = userEvent.setup();
    api.getItems.mockResolvedValue([arroz]);
    render(<App />);
    await user.click(await screen.findByTitle('Editar'));
    const row = screen.getByTitle('Guardar').closest('form');
    const [name, qty, price] = row.querySelectorAll('input');
    expect(name).toHaveValue('Arroz');
    await user.clear(name); await user.type(name, 'Arroz integral');
    await user.clear(qty); await user.type(qty, '5');
    await user.clear(price); await user.type(price, '2500');
    await user.click(screen.getByTitle('Guardar'));
    await waitFor(() =>
      expect(api.updateItem).toHaveBeenCalledWith(1, { name: 'Arroz integral', quantity: 5, price: 2500 }));
    await waitFor(() => expect(screen.queryByTitle('Guardar')).not.toBeInTheDocument());
  });

  it('cancelar la edición no llama a la API', async () => {
    const user = userEvent.setup();
    api.getItems.mockResolvedValue([arroz]);
    render(<App />);
    await user.click(await screen.findByTitle('Editar'));
    await user.click(screen.getByTitle('Cancelar'));
    expect(api.updateItem).not.toHaveBeenCalled();
    expect(screen.getByText('Arroz')).toBeInTheDocument();
  });

  it('muestra el error del backend', async () => {
    const user = userEvent.setup();
    api.getItems.mockResolvedValue([arroz]);
    api.deleteItem.mockRejectedValue(new Error('Producto 1 no existe'));
    render(<App />);
    await user.click(await screen.findByTitle('Eliminar'));
    expect(await screen.findByText('Producto 1 no existe')).toBeInTheDocument();
  });
});

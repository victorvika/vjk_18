import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import App from '../App';

// jsdom has no canvas, so stand in a minimal chart API for the panel.
vi.mock('lightweight-charts', () => {
  const series = {
    setData: vi.fn(),
    applyOptions: vi.fn(),
  };
  const chart = {
    addSeries: vi.fn(() => series),
    removeSeries: vi.fn(),
    applyOptions: vi.fn(),
    priceScale: vi.fn(() => ({ applyOptions: vi.fn() })),
    timeScale: vi.fn(() => ({ fitContent: vi.fn() })),
    subscribeCrosshairMove: vi.fn(),
    remove: vi.fn(),
  };
  return {
    createChart: vi.fn(() => chart),
    CandlestickSeries: { name: 'Candlestick' },
    HistogramSeries: { name: 'Histogram' },
    LineSeries: { name: 'Line' },
    AreaSeries: { name: 'Area' },
  };
});

describe('ChartDeck shell', () => {
  it('renders the ticker, watchlist and disclaimer with synthetic data', () => {
    const { container } = render(<App />);
    expect(container.querySelector('.brand-text')?.textContent).toBe('ChartDeck');
    expect(screen.getByLabelText('Watchlist')).toBeTruthy();
    expect(screen.getAllByText(/procedurally generated/i).length).toBeGreaterThan(0);
    expect(screen.getByLabelText('Order book (synthetic)')).toBeTruthy();
    expect(screen.getByLabelText('Time and sales (synthetic)')).toBeTruthy();
  });

  it('switches symbol from the watchlist', () => {
    render(<App />);
    const watch = screen.getByLabelText('Watchlist');
    fireEvent.click(within(watch).getByText('BTCUSDT'));
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('BTCUSDT');
  });

  it('changes timeframe when a toolbar button is pressed', () => {
    render(<App />);
    const tf = screen.getByRole('group', { name: 'Timeframe' });
    const daily = within(tf).getByRole('button', { name: '1D' });
    fireEvent.click(daily);
    expect(daily.getAttribute('aria-pressed')).toBe('true');
  });

  it('opens the command palette with the keyboard and runs a command', () => {
    render(<App />);
    fireEvent.keyDown(window, { key: 'k', metaKey: true });
    const input = screen.getByLabelText('Command search');
    fireEvent.change(input, { target: { value: 'ETHUSDT' } });
    const options = screen.getAllByRole('option');
    expect(options.length).toBeGreaterThan(0);
    fireEvent.click(options[0]);
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('ETHUSDT');
  });
});

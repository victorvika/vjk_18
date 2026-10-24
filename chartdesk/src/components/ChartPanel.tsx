import { useEffect, useRef, useState } from 'react';
import {
  CandlestickSeries,
  HistogramSeries,
  LineSeries,
  createChart,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
} from 'lightweight-charts';
import type { Candle } from '../lib/market';
import type { StudyRow } from '../lib/studies';

export type OverlayId = 'ema20' | 'ema50' | 'sma200' | 'vwap' | 'volume';

type Props = {
  candles: Candle[];
  overlays: StudyRow[];
  showVolume: boolean;
  symbol: string;
  loading: boolean;
};

const C = {
  up: '#26a69a',
  down: '#ef5350',
  grid: 'rgba(255,255,255,0.045)',
  axis: '#7d8794',
  crosshair: '#8b95a5',
  text: '#c9d1d9',
};

export default function ChartPanel({ candles, overlays, showVolume, symbol, loading }: Props) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeRef = useRef<ISeriesApi<'Histogram'> | null>(null);
  const overlayRefs = useRef(new Map<string, ISeriesApi<'Line'>>());
  const [ohlc, setOhlc] = useState<{ o: number; h: number; l: number; c: number } | null>(null);

  // create the chart exactly once
  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    const chart = createChart(host, {
      layout: {
        background: { color: 'transparent' },
        textColor: C.text,
        fontSize: 11,
        fontFamily:
          "'Inter var', 'Inter', ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif",
      },
      grid: { vertLines: { color: C.grid }, horzLines: { color: C.grid } },
      rightPriceScale: { borderColor: 'rgba(255,255,255,0.08)', scaleMargins: { top: 0.08, bottom: 0.26 } },
      timeScale: { borderColor: 'rgba(255,255,255,0.08)', timeVisible: true, secondsVisible: false, rightOffset: 4 },
      crosshair: {
        mode: 1,
        vertLine: { color: C.crosshair, width: 1, style: 3, labelBackgroundColor: '#2a3240' },
        horzLine: { color: C.crosshair, width: 1, style: 3, labelBackgroundColor: '#2a3240' },
      },
      handleScale: { axisPressedMouseMove: true },
      autoSize: true,
    });
    chartRef.current = chart;

    candleRef.current = chart.addSeries(CandlestickSeries, {
      upColor: C.up,
      downColor: C.down,
      borderUpColor: C.up,
      borderDownColor: C.down,
      wickUpColor: C.up,
      wickDownColor: C.down,
      priceLineColor: '#5b6573',
    });

    volumeRef.current = chart.addSeries(HistogramSeries, {
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume',
      color: 'rgba(120,140,170,0.35)',
    });
    chart.priceScale('volume').applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } });

    chart.subscribeCrosshairMove((param) => {
      const series = candleRef.current;
      if (!series) return;
      if (!param.time || !param.point) {
        setOhlc(null);
        return;
      }
      const bar = param.seriesData.get(series) as
        | { open: number; high: number; low: number; close: number }
        | undefined;
      if (bar) setOhlc({ o: bar.open, h: bar.high, l: bar.low, c: bar.close });
    });

    return () => {
      chart.remove();
      chartRef.current = null;
      candleRef.current = null;
      volumeRef.current = null;
      overlayRefs.current.clear();
    };
  }, []);

  // bars
  useEffect(() => {
    const series = candleRef.current;
    if (!series) return;
    series.setData(
      candles.map((c) => ({
        time: c.time as UTCTimestamp,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      })),
    );
    volumeRef.current?.setData(
      candles.map((c) => ({
        time: c.time as UTCTimestamp,
        value: c.volume,
        color: c.close >= c.open ? 'rgba(38,166,154,0.30)' : 'rgba(239,83,80,0.30)',
      })),
    );
    chartRef.current?.timeScale().fitContent();
  }, [candles]);

  // volume visibility
  useEffect(() => {
    volumeRef.current?.applyOptions({ visible: showVolume });
  }, [showVolume]);

  // overlays
  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;
    const wanted = new Map(overlays.map((o) => [o.id, o]));
    for (const [id, series] of overlayRefs.current) {
      if (!wanted.has(id)) {
        chart.removeSeries(series);
        overlayRefs.current.delete(id);
      }
    }
    for (const row of overlays) {
      let series = overlayRefs.current.get(row.id);
      if (!series) {
        series = chart.addSeries(LineSeries, {
          color: row.color,
          lineWidth: 1,
          priceLineVisible: false,
          lastValueVisible: false,
          crosshairMarkerVisible: false,
        });
        overlayRefs.current.set(row.id, series);
      }
      series.applyOptions({ color: row.color, title: row.label });
      series.setData(row.points.map((p) => ({ time: p.time as UTCTimestamp, value: p.value })));
    }
  }, [overlays]);

  const last = candles[candles.length - 1];

  return (
    <section className="chart-panel" aria-label="Price chart">
      <header className="chart-head">
        <div className="chart-title">
          <span className="sym">{symbol}</span>
          <span className="tf-badge">SYNTH</span>
        </div>
        <div className="ohlc-readout" aria-live="off">
          {last && (
            <>
              <span>
                O <b>{fmt(ohlc?.o ?? last.open)}</b>
              </span>
              <span>
                H <b>{fmt(ohlc?.h ?? last.high)}</b>
              </span>
              <span>
                L <b>{fmt(ohlc?.l ?? last.low)}</b>
              </span>
              <span>
                C <b className={last.close >= last.open ? 'up' : 'down'}>{fmt(ohlc?.c ?? last.close)}</b>
              </span>
            </>
          )}
        </div>
        <div className="chart-legend">
          {overlays.map((o) => (
            <span key={o.id} className="legend-item">
              <i style={{ background: o.color }} />
              {o.label}
            </span>
          ))}
        </div>
      </header>
      <div className="chart-host" ref={hostRef} data-testid="chart-host" />
      {loading && <div className="chart-loading">building session…</div>}
    </section>
  );
}

function fmt(v: number) {
  return v >= 1000 ? v.toFixed(2) : v.toFixed(v >= 1 ? 3 : 5);
}

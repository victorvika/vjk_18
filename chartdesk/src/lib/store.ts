import type { Candle } from './market';

const DB_NAME = 'chartdesk';
const DB_VERSION = 1;
const STORE = 'datasets';

export type Dataset = {
  id: string;
  name: string;
  symbol: string;
  barSeconds: number;
  importedAt: number;
  candles: Candle[];
  source: string;
};

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (typeof indexedDB === 'undefined') {
      reject(new Error('IndexedDB is unavailable in this browser.'));
      return;
    }
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE)) db.createObjectStore(STORE, { keyPath: 'id' });
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error ?? new Error('Could not open IndexedDB.'));
  });
}

export async function saveDataset(dataset: Dataset): Promise<void> {
  const db = await openDb();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE, 'readwrite');
    tx.objectStore(STORE).put(dataset);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error ?? new Error('Could not save dataset.'));
  });
  db.close();
}

export type DatasetMeta = Omit<Dataset, 'candles'> & { bars: number; from: number; to: number };

export async function listDatasets(): Promise<DatasetMeta[]> {
  const db = await openDb();
  const all = await new Promise<Dataset[]>((resolve, reject) => {
    const tx = db.transaction(STORE, 'readonly');
    const req = tx.objectStore(STORE).getAll();
    req.onsuccess = () => resolve(req.result as Dataset[]);
    req.onerror = () => reject(req.error ?? new Error('Could not read datasets.'));
  });
  db.close();
  return all
    .map(({ candles, ...meta }) => ({
      ...meta,
      bars: candles.length,
      from: candles[0]?.time ?? 0,
      to: candles.at(-1)?.time ?? 0,
    }))
    .sort((a, b) => b.importedAt - a.importedAt);
}

export async function getDataset(id: string): Promise<Dataset | null> {
  const db = await openDb();
  const found = await new Promise<Dataset | undefined>((resolve, reject) => {
    const tx = db.transaction(STORE, 'readonly');
    const req = tx.objectStore(STORE).get(id);
    req.onsuccess = () => resolve(req.result as Dataset | undefined);
    req.onerror = () => reject(req.error ?? new Error('Could not read dataset.'));
  });
  db.close();
  return found ?? null;
}

export async function deleteDataset(id: string): Promise<void> {
  const db = await openDb();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE, 'readwrite');
    tx.objectStore(STORE).delete(id);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error ?? new Error('Could not delete dataset.'));
  });
  db.close();
}

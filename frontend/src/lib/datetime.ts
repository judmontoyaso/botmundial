// Las fechas de partidos vienen del backend en UTC (timestamptz).
// Un partido a las 02:00Z se juega la noche anterior en hora de Colombia,
// así que nunca debe cortarse el string UTC para mostrar el día.

function parseUTC(iso: string): Date | null {
  if (!iso) return null;
  // Si el string no trae zona horaria, asumir UTC
  const hasTz = /Z$|[+-]\d{2}:?\d{2}$/.test(iso);
  const d = new Date(hasTz ? iso : `${iso}Z`);
  return isNaN(d.getTime()) ? null : d;
}

/** Fecha local del partido en formato YYYY-MM-DD (zona horaria del navegador). */
export function matchLocalDate(iso: string | null | undefined): string {
  const d = parseUTC(iso ?? '');
  if (!d) return '';
  return d.toLocaleDateString('sv-SE'); // sv-SE produce YYYY-MM-DD
}

/** Hora local del partido en formato HH:mm (zona horaria del navegador). */
export function matchLocalTime(iso: string | null | undefined): string {
  const d = parseUTC(iso ?? '');
  if (!d) return '';
  return d.toLocaleTimeString('es-CO', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });
}

/** Fecha local legible, ej. "jue, 11 jun". */
export function matchLocalDateLabel(iso: string | null | undefined): string {
  const d = parseUTC(iso ?? '');
  if (!d) return '';
  return d.toLocaleDateString('es-CO', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
  });
}

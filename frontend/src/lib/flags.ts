// FIFA 3-letter code → ISO 3166-1 alpha-2
const FIFA_TO_ISO2: Record<string, string> = {
  ARG: 'AR', BRA: 'BR', FRA: 'FR', ENG: 'GB', GER: 'DE', ITA: 'IT',
  ESP: 'ES', POR: 'PT', NED: 'NL', BEL: 'BE', URU: 'UY', MEX: 'MX',
  USA: 'US', COL: 'CO', CHI: 'CL', ECU: 'EC', PER: 'PE', VEN: 'VE',
  PAR: 'PY', BOL: 'BO', CRC: 'CR', HON: 'HN', PAN: 'PA', JAM: 'JM',
  TRI: 'TT', CAN: 'CA', MAR: 'MA', SEN: 'SN', GHA: 'GH', NGA: 'NG',
  CMR: 'CM', TUN: 'TN', ALG: 'DZ', EGY: 'EG', CIV: 'CI', MLI: 'ML',
  JPN: 'JP', KOR: 'KR', IRN: 'IR', AUS: 'AU', SAU: 'SA', QAT: 'QA',
  UAE: 'AE', IRQ: 'IQ', SUI: 'CH', AUT: 'AT', DEN: 'DK', SWE: 'SE',
  NOR: 'NO', POL: 'PL', CZE: 'CZ', SVK: 'SK', HUN: 'HU', ROU: 'RO',
  SRB: 'RS', CRO: 'HR', SVN: 'SI', GRE: 'GR', TUR: 'TR', UKR: 'UA',
  SCO: 'GB', WAL: 'GB', NIR: 'GB', IRL: 'IE', ISL: 'IS', ALB: 'AL',
  NMK: 'MK', MNE: 'ME', BIH: 'BA', GEO: 'GE', AZE: 'AZ', ARM: 'AM',
  KAZ: 'KZ', UZB: 'UZ', RSA: 'ZA', ZIM: 'ZW', MOZ: 'MZ', TAN: 'TZ',
  KEN: 'KE', ETH: 'ET', ANG: 'AO', COD: 'CD', COG: 'CG', GAB: 'GA',
  CHN: 'CN', IND: 'IN', PAK: 'PK', BAN: 'BD', SRI: 'LK', NEP: 'NP',
  THA: 'TH', VIE: 'VN', MAS: 'MY', IDN: 'ID', PHI: 'PH', SIN: 'SG',
  NZL: 'NZ', FIJ: 'FJ', PNG: 'PG', ISR: 'IL', LIB: 'LB', JOR: 'JO',
  SYR: 'SY', YEM: 'YE', OMA: 'OM', KUW: 'KW', BHR: 'BH',
};

export function getFlagUrl(teamCode: string): string {
  if (!teamCode) return '';
  const iso2 = FIFA_TO_ISO2[teamCode.toUpperCase()] || teamCode.slice(0, 2);
  return `https://flagcdn.com/w40/${iso2.toLowerCase()}.png`;
}

export function getFlagEmoji(teamCode: string): string {
  if (!teamCode) return '🏳️';
  const iso2 = FIFA_TO_ISO2[teamCode.toUpperCase()] || teamCode.slice(0, 2).toUpperCase();
  try {
    const points = [...iso2].map(c => 0x1f1e6 + c.charCodeAt(0) - 65);
    return String.fromCodePoint(...points);
  } catch {
    return '🏳️';
  }
}

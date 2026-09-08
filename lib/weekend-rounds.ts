type ScheduledFixture = { kickoff_time: string };

// Keep Friday–Monday fixtures together, including after the first game starts.
export function weekendKey(kickoff: string) {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Europe/London", year: "numeric", month: "2-digit", day: "2-digit",
  }).formatToParts(new Date(kickoff));
  const part = (name: string) => parts.find(p => p.type === name)!.value;
  const date = new Date(`${part("year")}-${part("month")}-${part("day")}T12:00:00Z`);
  date.setUTCDate(date.getUTCDate() - (date.getUTCDay() + 2) % 7);
  return date.toISOString().slice(0, 10);
}

export function groupWeekendFixtures<T extends ScheduledFixture>(fixtures: T[]) {
  const groups = new Map<string, T[]>();
  for (const fixture of [...fixtures].sort((a,b) => a.kickoff_time.localeCompare(b.kickoff_time))) {
    const key = weekendKey(fixture.kickoff_time);
    groups.set(key, [...(groups.get(key) || []), fixture]);
  }
  return Array.from(groups, ([key, rows]) => ({key, rows}));
}

export function defaultWeekend<T extends ScheduledFixture>(fixtures: T[], now = Date.now()) {
  const rounds = groupWeekendFixtures(fixtures);
  return rounds.find(round => round.rows.some(f => Date.parse(f.kickoff_time) >= now))?.key
    ?? "";
}

export function weekendLabel(fixtures: ScheduledFixture[]) {
  if (!fixtures.length) return "No upcoming fixtures";
  const dates = fixtures.map(f => new Date(f.kickoff_time)).sort((a,b) => +a - +b);
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric", month: "long", year: "numeric", timeZone: "Europe/London",
  }).formatRange(dates[0], dates[dates.length - 1]);
}

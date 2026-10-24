type FrozenCandidate = {
  home_n8: number | null;
  away_n8: number | null;
  candidate_home_lambda: number | string | null;
  candidate_away_lambda: number | string | null;
  candidate_calculated_at: string | null;
};

type ExactScore = {
  home: number;
  away: number;
  probability: number;
  tied: boolean;
};

function validLambda(value: unknown): number | null {
  if (typeof value !== "number" && typeof value !== "string") return null;
  if (typeof value === "string" && !value.trim()) return null;
  const number = Number(value);
  // The frozen candidate clamps lambdas to 0.15–4.5. Reject corrupt inputs.
  return Number.isFinite(number) && number >= 0.15 && number <= 4.5 ? number : null;
}

function poissonProbability(lambda: number, goals: number) {
  let probability = Math.exp(-lambda);
  for (let i = 1; i <= goals; i++) probability *= lambda / i;
  return probability;
}

// P(k+1) / P(k) = lambda / (k+1): the mode is floor(lambda).
// Positive integer lambdas have two modes (lambda-1, lambda); choose the lower.
// Independence means the joint maximum is the pair of marginal modes.
// Use full frozen precision, never rounded displayed xG or a truncated score grid.
export function predictedScore(
  kickoffTime: string,
  snapshot: FrozenCandidate | null,
  now: number,
): ExactScore | null {
  const kickoff = Date.parse(kickoffTime);
  if (!Number.isFinite(now) || !Number.isFinite(kickoff) || kickoff <= now || !snapshot) return null;
  if (![snapshot.home_n8, snapshot.away_n8].every(n => n !== null && Number.isInteger(n) && n >= 4 && n <= 8)) return null;
  const calculated = Date.parse(snapshot.candidate_calculated_at ?? "");
  if (!Number.isFinite(calculated) || calculated >= kickoff || calculated > now) return null;
  const homeLambda = validLambda(snapshot.candidate_home_lambda);
  const awayLambda = validLambda(snapshot.candidate_away_lambda);
  if (homeLambda === null || awayLambda === null) return null;
  const home = Math.ceil(homeLambda) - 1;
  const away = Math.ceil(awayLambda) - 1;
  return {
    home,
    away,
    probability: poissonProbability(homeLambda, home) * poissonProbability(awayLambda, away),
    tied: Number.isInteger(homeLambda) || Number.isInteger(awayLambda),
  };
}

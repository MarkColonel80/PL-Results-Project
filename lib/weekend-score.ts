type FrozenCandidate = {
  home_n8: number | null;
  away_n8: number | null;
  candidate_home_lambda: number | string | null;
  candidate_away_lambda: number | string | null;
  candidate_calculated_at: string | null;
  candidate_home_prob?: number | string | null;
  candidate_draw_prob?: number | string | null;
  candidate_away_prob?: number | string | null;
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

function sameProbability(a: number, b: number) {
  return Math.abs(a - b) <= Number.EPSILON * 8 * Math.max(a, b);
}

// Only the ranking is bounded, never the probability distribution.
// For k > ceil(lambda)+2, at least three smaller goal totals have higher
// Poisson mass. Such a tail score cannot enter the top three joint scores.
export function likelyScorelines(kickoffTime: string, snapshot: FrozenCandidate | null, now: number): ExactScore[] | null {
  if (!predictedScore(kickoffTime, snapshot, now) || !snapshot) return null;
  const homeLambda = Number(snapshot.candidate_home_lambda);
  const awayLambda = Number(snapshot.candidate_away_lambda);
  const scores: ExactScore[] = [];
  for (let home = 0; home <= Math.ceil(homeLambda) + 2; home++) {
    for (let away = 0; away <= Math.ceil(awayLambda) + 2; away++) {
      scores.push({home, away, probability: poissonProbability(homeLambda, home) * poissonProbability(awayLambda, away), tied: false});
    }
  }
  scores.sort((a, b) => sameProbability(a.probability, b.probability)
    ? (a.home + a.away) - (b.home + b.away) || a.home - b.home
    : b.probability - a.probability);
  return scores.slice(0, 3).map(score => ({
    ...score,
    tied: scores.some(other => other !== score && sameProbability(score.probability, other.probability)),
  }));
}

export function favouredOutcome(kickoffTime: string, snapshot: FrozenCandidate | null, now: number) {
  if (!predictedScore(kickoffTime, snapshot, now) || !snapshot) return null;
  const raw = [snapshot.candidate_home_prob, snapshot.candidate_draw_prob, snapshot.candidate_away_prob];
  if (raw.some(value => (typeof value !== "number" && typeof value !== "string") || (typeof value === "string" && !value.trim()))) return null;
  const probabilities = raw.map(Number);
  if (probabilities.some(value => !Number.isFinite(value) || value < 0 || value > 1)) return null;
  if (Math.abs(probabilities.reduce((sum, value) => sum + value, 0) - 1) > 1e-6) return null;
  const probability = Math.max(...probabilities);
  const labels = ["home", "draw", "away"] as const;
  // Display the saved H/D/A probabilities as they are: no recalculation or normalization.
  return {outcomes: labels.filter((_, index) => probabilities[index] === probability), probability};
}

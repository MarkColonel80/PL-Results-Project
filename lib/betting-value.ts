export function bettingValue(probability: number | null | undefined, decimalOdds: number | null | undefined) {
  if (probability == null || decimalOdds == null ||
      !Number.isFinite(probability) || !Number.isFinite(decimalOdds) ||
      probability < 0 || probability > 1 || decimalOdds <= 1) return null;

  const breakEvenProbability = 1 / decimalOdds;
  const percentagePoints = (probability - breakEvenProbability) * 100;
  const direction = percentagePoints > 1e-9 ? "positive" : percentagePoints < -1e-9 ? "negative" : "neutral";
  const magnitude = Math.abs(percentagePoints);
  const label = direction === "neutral" ? "0.0 pp" :
    `${direction === "positive" ? "+" : "−"}${magnitude < 0.05 ? "<0.1" : magnitude.toFixed(1)} pp`;

  return {breakEvenProbability, percentagePoints, direction, label};
}

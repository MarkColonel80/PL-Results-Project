import assert from "node:assert/strict";
import {bettingValue} from "../lib/betting-value.ts";

// The quoted price determines whether there is value, including its margin.
const city = bettingValue(0.49906324687675946, 2.4);
assert.equal(city.direction, "positive");
assert.equal(city.label, "+8.2 pp");
assert.ok(Math.abs(city.breakEvenProbability - 1 / 2.4) < 1e-12);

// 41% exceeds the displayed no-vig 40.7%, but is below the 41.7% needed at 2.40.
assert.equal(bettingValue(0.41, 2.4).direction, "negative");
assert.equal(bettingValue(0.5623729527080932, 1.75).label, "−0.9 pp");
assert.equal(bettingValue(0.4, 2.5).direction, "neutral");
assert.equal(bettingValue(0.40001, 2.5).label, "+<0.1 pp");
assert.equal(bettingValue(0.39999, 2.5).label, "−<0.1 pp");
for (const [p, odds] of [[null, 2.4], [0.5, null], [NaN, 2.4], [0.5, Infinity], [-0.1, 2.4], [1.1, 2.4], [0.5, 1], [0.5, 0]]) {
  assert.equal(bettingValue(p, odds), null);
}
console.log("Value indicators: price threshold, signs, rounding and unavailable values passed.");

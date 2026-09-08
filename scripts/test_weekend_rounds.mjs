import assert from "node:assert/strict";
import {defaultWeekend, groupWeekendFixtures, weekendKey} from "../lib/weekend-rounds.ts";

const fixtures = [
  {kickoff_time: "2026-09-04T19:00:00Z"},
  {kickoff_time: "2026-09-06T15:30:00Z"},
  {kickoff_time: "2026-09-12T14:00:00Z"},
  {kickoff_time: "2026-09-14T19:00:00Z"},
];
assert.deepEqual(groupWeekendFixtures(fixtures).map(g => g.rows.length), [2,2]);
assert.equal(defaultWeekend(fixtures, Date.parse("2026-09-08T12:00:00Z")), "2026-09-11");
assert.equal(defaultWeekend(fixtures, Date.parse("2026-09-13T12:00:00Z")), "2026-09-11");
assert.equal(defaultWeekend(fixtures, Date.parse("2026-09-15T12:00:00Z")), "");
assert.equal(defaultWeekend([]), "");
// The UK calendar day controls the group, including around BST and year boundaries.
assert.equal(weekendKey("2026-09-10T23:30:00Z"), "2026-09-11");
assert.equal(weekendKey("2027-01-04T20:00:00Z"), "2027-01-01");
console.log("Weekend grouping and default-selection checks passed.");

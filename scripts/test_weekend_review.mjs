import assert from "node:assert/strict";
import {weekendReviewWarnings,venueDefenceComparison} from "../lib/weekend-review.ts";

const odds={h:2.75,d:3.6,a:2.625};
const villa={h:.391,d:.253,a:.356};
const brentford={h:.326,d:.256,a:.418};
const disagreement=weekendReviewWarnings(villa,brentford,odds,8,8);
assert.equal(disagreement.length,2);
assert.ok(disagreement[0].startsWith("Home price"));
assert.ok(disagreement[1].startsWith("Away price"));
// The test concerns value at each quoted price, not which outcome is most likely.
assert.deepEqual(weekendReviewWarnings({h:.51,d:.25,a:.24},{h:.49,d:.26,a:.25},{h:1.5,d:3,a:3},8,8),[]);
assert.ok(weekendReviewWarnings({h:.41,d:.3,a:.29},{h:.43,d:.3,a:.27},{h:2.4,d:null,a:null},8,8)[0].startsWith("Home price"));
assert.deepEqual(weekendReviewWarnings(null,null,{h:null,d:null,a:null},8,8),[]);
assert.equal(weekendReviewWarnings(villa,brentford,odds,2,8).length,1);
assert.match(weekendReviewWarnings(villa,brentford,odds,null,8)[0],/Limited/);
assert.match(weekendReviewWarnings(null,null,odds,4,8)[0],/Partial/);
const bournemouth=venueDefenceComparison(8,.875,1.8009451795645057);
assert.equal(bournemouth.conceded,7);
assert.ok(Math.abs(bournemouth.xga-14.407561436516046)<1e-12);
for(const values of [[null,.8,1.8],[0,.8,1.8],[9,.8,1.8],[8,null,1.8],[8,.8,NaN],[8,-1,1.8]])assert.equal(venueDefenceComparison(...values),null);
console.log("Weekend review: conflicting price assessments, limited history and conceded/xGA totals passed.");

import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {paperEventIssues,ledgerPrefixUnchanged} from "../lib/weekend-paper.ts";
const ledger=JSON.parse(readFileSync(new URL("../data/weekend-paper-ledger.json",import.meta.url),"utf8"));
assert.equal(ledger.version,1);assert.equal(ledger.mode,"paper");assert.equal(ledger.unit_stake,1);
assert.equal(new Set(ledger.fixtures.map(f=>f.fixture_id)).size,ledger.fixtures.length,"Duplicate ledger fixture");
assert.equal(new Set(ledger.events.map(e=>e.id)).size,ledger.events.length,"Duplicate decision ID");
for(const e of ledger.events){
 const f=ledger.fixtures.find(f=>f.fixture_id===e.fixture_id);
 assert.ok(f,"Decision has no fixture");assert.ok(["watch","pass","paper"].includes(e.status));
 assert.deepEqual(paperEventIssues(e,f),[],e.id);
}
if(process.argv[2]){
 const previous=JSON.parse(readFileSync(process.argv[2],"utf8"));
 assert.ok(ledgerPrefixUnchanged(previous,ledger),"Original fixtures, decisions or settlements were rewritten; append new records instead");
}
console.log(`Paper ledger valid: ${ledger.events.length} timestamped decisions. ${process.argv[2]?"Append-only history verified.":"Pass the previous ledger path to check append-only history before a later publish."}`);

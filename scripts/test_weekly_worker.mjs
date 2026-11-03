import assert from "node:assert/strict";
import {validateClaims} from "../lib/weekly-identity.ts";
const c={iss:"https://token.actions.githubusercontent.com",aud:"pl-results-project-weekly",repository:"MarkColonel80/PL-Results-Project",repository_id:"1346031407",ref:"refs/heads/main",workflow_ref:"MarkColonel80/PL-Results-Project/.github/workflows/pl-weekly-cloud.yml@refs/heads/main",runner_environment:"github-hosted",event_name:"push",run_id:"123",sha:"abc",iat:1000,nbf:1000,exp:1300};
assert.equal(validateClaims(c,1100).runId,"123");
for(const [key,value] of Object.entries({iss:"evil",aud:"wrong",repository:"other/repo",repository_id:"1",ref:"refs/heads/pr",workflow_ref:"other.yml",runner_environment:"self-hosted",event_name:"pull_request",run_id:"abc",exp:100,nbf:1400,iat:1400}))assert.throws(()=>validateClaims({...c,[key]:value},1100),key);
console.log("Worker identity rejects other repositories, branches, workflows, event types and expired tokens.");

import {review,current,futureArchive} from "./weekly/review.mjs";
import {readFileSync} from "node:fs";
const a=JSON.parse(readFileSync("data/weekend-2026-11-06-snapshots.json","utf8"));
for(const f of a.fixtures){const p=current(f.snapshot);for(const k of ["h","d","a"])assert.ok(Math.abs(p[k]-f.current[k])<1e-12);}
console.log("Weekly current-model derivation matches all 10 frozen regression fixtures without altering model code.");

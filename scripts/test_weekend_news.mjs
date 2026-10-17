import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {parseWeekendNews,WEEKEND_NEWS_MARKER} from "../lib/weekend-review.ts";

for(const notes of [null,"legacy provenance",WEEKEND_NEWS_MARKER+"{broken",WEEKEND_NEWS_MARKER+"[]"]){
 assert.equal(parseWeekendNews(notes),null);
}
const record={checkedAt:"2026-10-17T14:14:39Z",home:"Home news",away:"Away news",schedule:"Thursday Europe",teams:"Teams pending",availability:[],sources:[{label:"Club",url:"https://example.com/news"}]};
const pack=x=>"original provenance"+WEEKEND_NEWS_MARKER+JSON.stringify(x);
assert.equal(parseWeekendNews(pack(record)).home,"Home news");
assert.equal(parseWeekendNews(pack({...record,checkedAt:"invalid"})),null);
assert.equal(parseWeekendNews(pack({...record,home:[]})),null);
assert.equal(parseWeekendNews(pack({...record,sources:[{label:"Bad",url:"javascript:alert(1)"}]})),null);
assert.equal(parseWeekendNews(pack({...record,sources:[{label:"Bad",url:"https://user:password@example.com"}]})),null);
const data=JSON.parse(readFileSync(new URL("../data/weekend-2026-10-17-news.json",import.meta.url)));
assert.equal(data.fixtures.length,6);
assert.deepEqual([...data.preserved_started_fixtures].sort((a,b)=>a-b),[62,64,65,67]);
for(const fixture of data.fixtures){
 const news=parseWeekendNews(fixture.notes);
 assert.ok(news,fixture.fixture_id);
 assert.equal(news.checkedAt,data.checked_at);
 assert.equal(news.availability.length,2);
 assert.ok(news.sources.length>=3);
}
console.log("Weekend news: six real fixture records, legacy/malformed data, dates and unsafe links passed.");

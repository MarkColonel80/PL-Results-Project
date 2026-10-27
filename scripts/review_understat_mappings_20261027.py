"""Replay the dated identity review from frozen evidence; performs no database writes.

118 automatically unique matches are expected. Three ambiguous pairs require the
separate native-role evidence recorded in the reconciliation report.
"""
import ast,json,math,collections,argparse
from pathlib import Path
parser=argparse.ArgumentParser()
parser.add_argument('--inputs',default='data/understat-reconciliation-inputs-2026-10-27.json')
parser.add_argument('--output',required=True)
args=parser.parse_args()
evidence=json.loads(Path(args.inputs).read_text())
def unpack(table):return [dict(zip(table['columns'],row)) for row in table['rows']]
tree=ast.parse(open("scripts/resolve_understat_cross_source.py").read())
ns={"math":math}
for n in tree.body:
 if isinstance(n,ast.Assign) and all(isinstance(t,ast.Name) for t in n.targets):
  try:exec(compile(ast.Module(body=[n],type_ignores=[]),"<existing resolver>","exec"),ns)
  except:pass
 if isinstance(n,ast.FunctionDef) and n.name in ["I","score_candidate","clearly_unique","season_start"]:
  exec(compile(ast.Module(body=[n],type_ignores=[]),"<existing resolver>","exec"),ns)
source=[r for r in unpack(evidence["source"]) if ns["I"](r["minutes_played"])>0];base=[r for r in unpack(evidence["core"]) if ns["I"](r["minutes_played"])>0]
by_source=collections.defaultdict(list);by_code=collections.defaultdict(list);by_match=collections.defaultdict(set)
for r in source:by_source[r["source_player_id"]].append(r)
for r in base:by_code[r["player_code"]].append(r);by_match[r["match_id"]].add(r["player_code"])
aliases={"Bournemouth":"AFC Bournemouth","Brighton":"Brighton & Hove Albion","Leeds":"Leeds United","Man City":"Manchester City","Man Utd":"Manchester United","Newcastle":"Newcastle United","Nott'm Forest":"Nottingham Forest","Spurs":"Tottenham Hotspur","Wolves":"Wolverhampton Wanderers","West Ham":"West Ham United","West Bromwich Albion":"West Brom","Manchester United":"Manchester United"}
norm=lambda x:aliases.get(x,x)
reviews=[];proposed={};ambiguous=[]
for pid,allrows in sorted(by_source.items()):
 rows=[r for r in allrows if ns["season_start"](r["season"])>=2015]
 if len(rows)<3:continue
 seasons={r["season"] for r in rows};codes=set.union(*(by_match[r["match_id"]] for r in rows))
 ranked=[]
 for code in codes:
  cr=[r for r in by_code[code] if r["season"] in seasons]
  score=ns["score_candidate"](rows,cr)
  if score:
   src={r["match_id"]:r for r in rows};dst={r["match_id"]:r for r in cr};common=src.keys()&dst.keys()
   team_mismatches=sum(norm(src[m]["team_name"])!=norm(dst[m]["team_name"]) for m in common)
   if team_mismatches:continue
   score["team_mismatches"]=team_mismatches
   score["shot_matches"]=sum(src[m]["shots"] is not None and dst[m]["shots"] is not None and int(src[m]["shots"])==int(dst[m]["shots"]) for m in common)
   score["nonzero_minutes"]=sum(ns["I"](src[m]["minutes_played"])>0 and ns["I"](dst[m]["minutes_played"])>0 for m in common)
   ranked.append((code,score))
 ranked.sort(key=lambda item:(-item[1]["common"],item[1]["goal_mismatches"],item[1]["avg_min_diff"],-min(item[1]["source_coverage"],item[1]["candidate_coverage"]),item[0]))
 if not ranked:continue
 if not ns["clearly_unique"](ranked[0],ranked[1] if len(ranked)>1 else None):
  ambiguous.append({"source_player_id":pid,"name_for_qa":rows[0]["player_name"],"candidates":ranked});continue
 code,score=ranked[0]
 # Additional conservative review gate; no rule in the existing resolver is relaxed.
 if score["goal_mismatches"]!=0 or score["nonzero_minutes"]<3:continue
 proposed[pid]=(code,score)
targets=collections.defaultdict(list)
for pid,(code,score) in proposed.items():targets[code].append(pid)
for pid,(code,score) in proposed.items():
 if len(targets[code])!=1:continue
 rows=by_source[pid];cr=by_code[code]
 reviews.append({"source_player_id":pid,"player_code":code,"score":score,"source_name_for_qa":rows[0]["player_name"],"canonical_name_for_qa":cr[0]["player_name"],"source_rows":len(rows),"seasons":sorted({r["season"] for r in rows}),"current_rows":sum(r["season"]=="2026/27" for r in rows)})
json.dump({"method":"existing canonical_match_history_goals_minutes_v1, with exact goals/team and positive-minute review gates","source_rows":len(source),"base_rows":len(base),"candidates":reviews,"ambiguous":ambiguous},open(args.output,"w"),indent=2)
print(json.dumps({"verified_candidates":len(reviews),"affected_rows":sum(r["source_rows"] for r in reviews),"current_rows":sum(r["current_rows"] for r in reviews),"ambiguous":len(ambiguous)}))
for r in reviews:print(json.dumps({k:r[k] for k in ["source_player_id","player_code","source_name_for_qa","canonical_name_for_qa","score"]}))

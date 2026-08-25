"use client";
const recent=["2025/26","2026/27"];
const fplHistory=Array.from({length:11},(_,i)=>`${2016+i}/${String(17+i).padStart(2,"0")}`);
const footballHistory=["2012/13","2013/14",...Array.from({length:12},(_,i)=>`${2015+i}/${String(16+i).padStart(2,"0")}`)];
export default function SeasonSelect({season,onChange,includeHistory=false,includeFootballHistory=false}:{season:string,onChange:(s:string)=>void,includeHistory?:boolean,includeFootballHistory?:boolean}){
 const seasons=includeFootballHistory?[...footballHistory].reverse():includeHistory?[...fplHistory].reverse():recent;
 return <select value={season} onChange={e=>onChange(e.target.value)}>{seasons.map(s=><option value={s} key={s}>{s}</option>)}</select>
}
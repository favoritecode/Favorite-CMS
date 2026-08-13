"use client";
import { FormEvent, useState } from "react";
export default function Explore(){
  const [result,setResult]=useState("No results yet");
  async function submit(e:FormEvent<HTMLFormElement>){e.preventDefault();const f=new FormData(e.currentTarget);const kind=String(f.get("kind"));const q=new URLSearchParams(kind==="search"?{kind,q:String(f.get("q"))}:{kind,locale:String(f.get("locale")),key:String(f.get("key"))});const r=await fetch(`/explore/transport?${q}`);const p=await r.json();setResult(r.ok?JSON.stringify(p.data):String(p.error));}
  return <main className="p-8"><h1>Explore Favorite CMS</h1><form onSubmit={submit}><label>Workflow<select name="kind"><option value="search">Search</option><option value="localization">Localization</option></select></label><label>Query<input name="q"/></label><label>Locale<input name="locale" defaultValue="fr"/></label><label>Translation key<input name="key" defaultValue="public.welcome"/></label><button>Run</button></form><output aria-label="Result">{result}</output></main>
}

const fs = require('fs'), path = require('path'), os = require('os');
const { chromium } = require('playwright');
const specPath = process.argv[2], out = process.argv[3];
if (!specPath || !out) throw new Error('usage: conflux-video-capture.cjs SCENES.json OUTPUT_DIR');
const spec = JSON.parse(fs.readFileSync(specPath, 'utf8'));
const dirs = ['core-demo','t3-options','t4-options','stretch-deltas','screenshots'];
for (const d of dirs) fs.mkdirSync(path.join(out,d), {recursive:true});
const esc = s => String(s ?? '').replaceAll('|','\\|').replaceAll('\n',' ');
const sleep = ms => new Promise(r => setTimeout(r,ms));
(async () => {
 const browser = await chromium.launch({headless:true});
 const readJson=(file,fallback)=>{try{return JSON.parse(fs.readFileSync(file,'utf8'));}catch{return fallback;}};
 const manifestFile=path.join(out,'SHOT_MANIFEST.json'), narrationFile=path.join(out,'NARRATION_DRAFT.json'), baselineFile=path.join(out,'FOOTAGE_BASELINE.yaml');
 const manifest=(readJson(manifestFile,{clips:[]}).clips||[]), narration=(readJson(narrationFile,{scenes:[]}).scenes||[]), baseline=readJson(baselineFile,{version:1,scenes:[]});
 baseline.captured_at=new Date().toISOString();
 try {
  for (const scene of spec.scenes) {
   const category = scene.category || 'core'; const folder = category==='core'?'core-demo':category==='T3'?'t3-options':category==='T4'?'t4-options':'stretch-deltas';
   const clip = `${String(scene.id).replace(/[^a-zA-Z0-9_-]/g,'_')}.webm`, clipPath=path.join(out,folder,clip); let page,context;
   const began=Date.now(); let video; const tempVideoDir=fs.mkdtempSync(path.join(os.tmpdir(),'conflux-video-'));
   try {
    context=await browser.newContext({viewport:{width:1920,height:1080},deviceScaleFactor:1,locale:'en-US',timezoneId:'UTC',reducedMotion:'reduce',recordVideo:{dir:tempVideoDir,size:{width:1920,height:1080}}});
    page=await context.newPage(); video=page.video(); await page.goto(scene.url,{waitUntil:'networkidle',timeout:45000}); await sleep(1500);
    for (const a of (scene.actions||[])) {
     if(a.type==='goto') await page.goto(a.url,{waitUntil:'networkidle'});
     else if(a.type==='click') await page.locator(a.selector).click({timeout:15000});
     else if(a.type==='fill') await page.locator(a.selector).fill(a.value);
     else if(a.type==='scroll') { await page.evaluate(y=>window.scrollBy({top:y,behavior:'smooth'}),a.pixels||600); await sleep(a.hold_ms||1500); }
     else if(a.type==='wait') await sleep(a.ms||1000);
     else throw new Error('unsupported action type '+a.type);
     if(a.pause_before_ms) await sleep(a.pause_before_ms);
     if(a.pause_after_ms) await sleep(a.pause_after_ms);
    }
    await sleep(scene.end_hold_ms||3000); await page.screenshot({path:path.join(out,'screenshots',clip.replace('.webm','.png')),fullPage:false});
   } catch(e) { manifest.splice(0,manifest.length,...manifest.filter(x=>x.clip!==clip)); manifest.push({clip,category,feature:scene.beat,status:'FAILED',error:String(e)}); console.error(`scene ${scene.id} failed: ${e}`); }
   finally { if(context) await context.close(); if(video) { try { await video.saveAs(clipPath); } catch(e) { console.error(`video save failed ${scene.id}: ${e}`); } } fs.rmSync(tempVideoDir,{recursive:true,force:true}); }
   const duration=(Date.now()-began)/1000;
   if(!manifest.some(x=>x.clip===clip&&x.status==='FAILED')) {
    const actions=(scene.actions||[]).map(a=>`${a.type}${a.selector?' '+a.selector:''}`).join('; ');
    manifest.splice(0,manifest.length,...manifest.filter(x=>x.clip!==clip)); manifest.push({clip,category,feature:scene.beat,role:scene.role,route:scene.route,seed:scene.seed,start_state:scene.start_state,actions,end_state:scene.end_state,raw_duration_seconds:duration,recommended_narration_seconds:Math.round(duration/1.3),why_it_matters:scene.why,replacement_status:'baseline'});
    narration.splice(0,narration.length,...narration.filter(x=>x.scene!==scene.beat)); narration.push({scene:scene.beat,target_seconds:Math.round(duration/1.3),main_point:scene.main_point||scene.why,draft:scene.narration||'',shorter:scene.shorter||'',clips:[clip]});
    baseline.scenes=baseline.scenes.filter(x=>x.id!==scene.id); baseline.scenes.push({id:scene.id,route:scene.route,feature:scene.beat,role:scene.role,screenshot:`screenshots/${clip.replace('.webm','.png')}`,key_actions:(scene.actions||[]).map(a=>a.selector).filter(Boolean)});
   }
   const partial={version:1,generated_at:new Date().toISOString(),clips:manifest};
   fs.writeFileSync(path.join(out,'SHOT_MANIFEST.md'),'# Shot manifest\n\n'+manifest.map(m=>`## ${m.clip}\n\n- Feature/story beat: ${esc(m.feature)}\n- Category: ${esc(m.category)}\n- Role: ${esc(m.role)}\n- Route: ${esc(m.route)}\n- Seed/demo state: ${esc(m.seed)}\n- Start: ${esc(m.start_state)}\n- Actions: ${esc(m.actions)}\n- End: ${esc(m.end_state)}\n- Raw duration: ${m.raw_duration_seconds??'n/a'}s\n- Narration: ${m.recommended_narration_seconds??'n/a'}s\n- Why it matters: ${esc(m.why_it_matters)}\n- Replacement status: ${esc(m.replacement_status||'failed; retry scene')}\n- Status: ${esc(m.status||'captured')}\n`).join('\n'));
   fs.writeFileSync(path.join(out,'NARRATION_DRAFT.md'),'# Narration draft (text only; no audio generated)\n\n'+narration.map(n=>`## ${n.scene} — ${n.target_seconds}s\n\n${n.draft}\n\nShorter: ${n.shorter}\n\nSupported by: ${n.clips.join(', ')}\n`).join('\n'));
   fs.writeFileSync(narrationFile,JSON.stringify({version:1,generated_at:new Date().toISOString(),scenes:narration},null,2));
   fs.writeFileSync(baselineFile,JSON.stringify(baseline,null,2));
   fs.writeFileSync(path.join(out,'FOOTAGE_STATUS.md'),`# Footage status\n\nCaptured ${manifest.filter(x=>!x.status).length}; failed ${manifest.filter(x=>x.status==='FAILED').length}. Failed scenes remain available for scene-only retry.\n`);
   fs.writeFileSync(manifestFile,JSON.stringify({version:1,generated_at:new Date().toISOString(),clips:manifest},null,2));
  }
  if(manifest.some(x=>x.status==='FAILED')) process.exitCode=1;
 } finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exit(2)});

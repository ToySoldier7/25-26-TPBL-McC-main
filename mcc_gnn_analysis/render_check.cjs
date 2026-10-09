// Local rendering/QA only. Run with the bundled Node and playwright package.
const fs=require('fs');
const path=require('path');
const {pathToFileURL}=require('url');
const {chromium}=require(process.env.PLAYWRIGHT_PACKAGE || 'C:/Users/junhy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{
 const root=__dirname;
 const out=path.join(root,'output','playwright');fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({headless:true,channel:'msedge'});
 const page=await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1});
 const errors=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.goto(pathToFileURL(path.join(root,'mcc_gnn_report.html')).href);
 await page.locator('#candidateRows tr').first().waitFor();
 async function capture(target,options){
   for(let attempt=0;attempt<3;attempt++){
     try{return await target.screenshot(options)}catch(e){if(attempt===2)throw e;await page.waitForTimeout(400)}
   }
 }
 await capture(page,{path:path.join(out,'desktop.png'),fullPage:true});
 const initial=await page.locator('#candidateRows tr').count();
 if(initial!==32)throw Error('Expected 32 new candidates, got '+initial);
 const first=await page.locator('#candidateRows tr').first().innerText();
 await page.locator('#query').fill('Tshimanga');
 if(await page.locator('#candidateRows tr').count()!==1)throw Error('Search failed');
 await page.locator('#query').fill('');
 await page.locator('#existing').check();
 if(await page.locator('#candidateRows tr').count()!==35)throw Error('Existing filter failed');
 await page.locator('#criterion').selectOption('individual');
 const individualFirst=await page.locator('#candidateRows tr').first().innerText();
 await page.reload();
 if(await page.locator('#criterion').inputValue()!=='individual')throw Error('URL state failed');
 await page.locator('#existing').uncheck();await page.locator('#criterion').selectOption('team');
 const linkErrors=await page.locator('a[href]').evaluateAll(links=>links.map(a=>a.getAttribute('href')).filter(h=>h&&!h.startsWith('#')&&!h.startsWith('http')));
 const missing=linkErrors.filter(h=>!fs.existsSync(path.join(root,h)));
 if(missing.length)throw Error('Missing links: '+missing);
 await page.setViewportSize({width:390,height:844});
 await capture(page,{path:path.join(out,'mobile.png'),fullPage:true});
 const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
 if(overflow)throw Error('Page-level mobile overflow');
 for(const f of fs.readdirSync(path.join(root,'figures')).filter(x=>x.endsWith('.svg'))){
   await page.goto(pathToFileURL(path.join(root,'figures',f)).href);
   const box=(await page.locator('svg').getAttribute('viewBox')).split(' ').map(Number);
   await page.setViewportSize({width:1400,height:Math.round(box[3]*1.4)});
   await capture(page.locator('svg'),{path:path.join(root,'figures',f.replace('.svg','.png'))});
 }
 const result={browser:'Microsoft Edge via Playwright',desktop:[1440,1000],mobile:[390,844],candidateRows:initial,teamFirst:first,individualFirst,pageErrors:errors,mobilePageOverflow:overflow,missingLocalLinks:missing,checks:['search','existing toggle','criterion sorting','URL reload persistence','figure rendering']};
 fs.writeFileSync(path.join(root,'qa_results.json'),JSON.stringify(result,null,2));
 if(errors.length)throw Error(errors.join('\n'));
 await browser.close();console.log(JSON.stringify(result,null,2));
})().catch(e=>{console.error(e);process.exit(1)});

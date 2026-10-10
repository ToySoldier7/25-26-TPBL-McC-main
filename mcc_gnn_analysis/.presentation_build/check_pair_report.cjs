const fs=require('fs'),path=require('path');
const {pathToFileURL}=require('url');
const {chromium}=require('C:/Users/junhy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{
 const root=path.resolve(__dirname,'..');const out=path.join(__dirname,'pair_report_qa');fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({headless:true,channel:'msedge'});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});const errors=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.goto(pathToFileURL(path.join(root,'foreign_pair_analysis','외국인_조합_분석.html')).href);
 await page.locator('img').evaluateAll(xs=>Promise.all(xs.map(x=>x.decode())));await page.evaluate(()=>document.fonts.ready);
 if(await page.locator('img').count()!==4)throw Error('Expected four embedded figures');
 const table=page.locator('section').last().locator('tbody tr');if(await table.count()!==48)throw Error('Expected all 48 imports');
 const text=await page.locator('body').innerText();for(const word of ['23.5','14.9','19회','200분 미만 12명','+0.52'])if(!text.includes(word))throw Error('Missing result '+word);
 await page.screenshot({path:path.join(out,'desktop.png')});
 await page.setViewportSize({width:390,height:844});if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Mobile viewport overflow');
 await page.screenshot({path:path.join(out,'mobile.png')});if(errors.length)throw Error(errors.join('\n'));
 fs.writeFileSync(path.join(out,'checks.json'),JSON.stringify({embedded_figures:4,foreign_players:48,mobile_overflow:false,page_errors:errors},null,2));
 await browser.close();console.log('Report render checks passed');
})().catch(e=>{console.error(e);process.exit(1)});

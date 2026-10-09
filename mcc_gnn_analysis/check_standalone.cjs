const fs=require('fs'),path=require('path'),os=require('os');
const {pathToFileURL}=require('url');
const {chromium}=require(process.env.PLAYWRIGHT_PACKAGE||'C:/Users/junhy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{
 const folder=fs.mkdtempSync(path.join(os.tmpdir(),'mcc-report-standalone-'));
 const file=path.join(folder,'report.html');fs.copyFileSync(path.join(__dirname,'mcc_gnn_report.html'),file);
 const browser=await chromium.launch({headless:true,channel:'msedge'});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000},offline:true});
  const errors=[],external=[];page.on('pageerror',e=>errors.push(String(e)));
  page.on('request',r=>{if(!r.url().startsWith('data:')&&r.url()!==pathToFileURL(file).href)external.push(r.url())});
  await page.goto(pathToFileURL(file).href);
  const images=await page.locator('img').evaluateAll(xs=>{xs.forEach(x=>x.loading='eager');return Promise.all(xs.map(async x=>{await x.decode();return {embedded:x.src.startsWith('data:image/'),loaded:x.complete&&x.naturalWidth>0}}))});
  if(images.length!==8||images.some(x=>!x.embedded||!x.loaded))throw Error('Embedded image check failed');
  if(external.length||errors.length)throw Error(JSON.stringify({external,errors}));
  if(await page.locator('#candidateRows tr').count()!==35)throw Error('Candidate count');
  await page.locator('#candidateSearch').fill('Daye');if(await page.locator('#candidateRows tr').count()!==1)throw Error('Standalone search');
  await page.locator('#candidateSearch').fill('');await page.locator('#roleFilter').selectOption('role');if(await page.locator('#candidateRows tr').count()!==23)throw Error('Standalone role filter');
  const downloads=await page.locator('a[download]').count();if(downloads!==16)throw Error('Figure downloads');
  const out=path.join(__dirname,'v2','qa_v3');fs.mkdirSync(out,{recursive:true});
  await page.locator('#results').screenshot({path:path.join(out,'standalone_images.png')});
  fs.writeFileSync(path.join(out,'standalone_checks.json'),JSON.stringify({isolated_html_only:true,offline:true,images:images.length,figure_downloads:downloads,external_requests:external,page_errors:errors,candidates:35,search:true,role_filter:true},null,2));
  console.log('Isolated HTML: 8 images and 16 downloads embedded; offline rendering and filters passed');
 }finally{await browser.close();fs.unlinkSync(file);fs.rmdirSync(folder)}
})().catch(e=>{console.error(e);process.exit(1)});

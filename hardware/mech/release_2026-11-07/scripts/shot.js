const {chromium}=require('playwright');
(async()=>{const [,, html,out,w,h]=process.argv;const br=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
const pg=await br.newPage({viewport:{width:+w,height:+h}});await pg.goto('file://'+html);await pg.waitForFunction('window.done===1',null,{timeout:120000});await pg.locator('#c').screenshot({path:out});await br.close();})();

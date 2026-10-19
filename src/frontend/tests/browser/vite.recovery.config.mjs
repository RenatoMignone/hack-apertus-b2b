// Test-only loopback proxy. Start the disposable smoke API on 8014 first.
import config from '../../vite.config.ts';
import fs from 'node:fs';
fs.mkdirSync(new URL('../../../../.local/recovery/', import.meta.url), {recursive:true});
const control = new URL('../../../../.local/recovery/fault.json', import.meta.url);
const counts = new URL('../../../../.local/recovery/counts.json', import.meta.url);
const faultPlugin = {name:'isolated-recovery-faults', configureServer(server) {
  server.middlewares.use((req,res,next) => {
    if (!req.url?.startsWith('/api/v1/')) return next();
    const key=req.method==='POST' && req.url.endsWith('/exports')?'export_submissions':
      req.url.includes('/operations/')?'operation_reads':null;
    if(key){let c={};try{c=JSON.parse(fs.readFileSync(counts,'utf8'));}catch{}c[key]=(c[key]??0)+1;fs.writeFileSync(counts,JSON.stringify(c));}
    let f;try{f=JSON.parse(fs.readFileSync(control,'utf8'));}catch{return next();}
    if (f.remaining>0 && req.method===(f.method??'GET') && req.url.includes(f.path)) {
      f.remaining--;fs.writeFileSync(control,JSON.stringify(f));
      res.statusCode=f.status??503;res.setHeader('Content-Type','application/json');
      res.end(JSON.stringify({schema_version:'1',request_id:'synthetic-recovery-fault',error:{code:f.code??'service_unavailable',retryable:true}}));return;
    }
    next();
  });
}};
export default {...config, plugins:[...config.plugins,faultPlugin],server:{...config.server,proxy:{'/api':{target:'http://127.0.0.1:8014',changeOrigin:true}}}};

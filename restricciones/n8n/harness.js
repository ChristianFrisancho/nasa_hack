const fs=require('fs'); const rows=JSON.parse(fs.readFileSync(process.argv[2]));
const $input={all:()=>rows.map(r=>({json:r}))};
const code=fs.readFileSync(require('path').join(__dirname,'validar_contrato.js'),'utf8');
const out=(new Function('$input',code))($input);
const j=out[0].json; j.primeros_errores=j.primeros_errores.slice(0,5); console.log(JSON.stringify(j,null,1));

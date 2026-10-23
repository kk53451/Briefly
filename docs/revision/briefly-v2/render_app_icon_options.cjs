const path=require('path');
const sharp=require(process.env.BRIEFLY_SHARP_PATH||'sharp');
const root=path.join(__dirname,'assets');
(async()=>{
  for(const name of ['full-name','b-dot']) {
    for(const size of [32,48,64,128,256,1024]) {
      await sharp(path.join(root,`app-icon-${name}.svg`),{density:800}).resize(size,size).png().toFile(path.join(root,`app-icon-${name}-${size}.png`));
    }
    await sharp(path.join(root,`app-icon-${name}-square.svg`),{density:800}).resize(1024,1024).png().toFile(path.join(root,`app-icon-${name}-square-1024.png`));
  }
  console.log('Rendered two app icon options at actual comparison sizes.');
})().catch(error=>{console.error(error);process.exit(1);});

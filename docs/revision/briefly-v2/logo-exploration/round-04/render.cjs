const fs=require('fs'),path=require('path');
const sharp=require(process.env.BRIEFLY_SHARP_PATH||'sharp');
const root=__dirname;
(async()=>{
  for(const file of fs.readdirSync(path.join(root,'assets')).filter(f=>f.endsWith('.svg'))){
    if(file.endsWith('-wordmark.svg')){
      await sharp(path.join(root,'assets',file),{density:240}).resize(1200,384).png().toFile(path.join(root,'assets',file.replace('.svg','-1200.png')));
    }else{
      for(const size of [48,64,128,1024])await sharp(path.join(root,'assets',file),{density:Math.max(size,100)}).resize(size,size).png().toFile(path.join(root,'assets',file.replace('.svg',`-${size}.png`)));
    }
  }
  await sharp(path.join(root,'comparison.svg')).png().toFile(path.join(root,'comparison.png'));
  console.log('Rendered 6 wordmark PNGs, 24 app icon PNGs, comparison.png.');
})().catch(e=>{console.error(e);process.exit(1);});

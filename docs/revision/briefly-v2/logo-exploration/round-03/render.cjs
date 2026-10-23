// Rasterize the code-native SVG artwork using bundled sharp. No raster edits.
const fs=require('fs');
const path=require('path');
const sharp=require(process.env.BRIEFLY_SHARP_PATH||'sharp');
const root=__dirname;
(async()=>{
  const icons=fs.readdirSync(path.join(root,'assets')).filter(name=>name.endsWith('-app-icon.svg'));
  for(const file of icons){
    for(const size of [16,24,32,64,1024]){
      await sharp(path.join(root,'assets',file),{density:Math.max(72,size)}).resize(size,size).png().toFile(path.join(root,'assets',file.replace('.svg',`-${size}.png`)));
    }
  }
  await sharp(path.join(root,'comparison.svg')).png().toFile(path.join(root,'comparison.png'));
  console.log(`Rendered ${icons.length} concepts at 16/24/32/64/1024px and comparison.png.`);
})().catch(error=>{console.error(error);process.exit(1);});
